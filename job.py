#!/usr/bin/env python3
"""OpenJDK JEP lifecycle census, run 1.

Downloads every issue of type JEP from the public JDK Bug System (JBS) REST API,
with its status history, and computes the pre-registered statistics in PREREG.md
(P1-P4 and the descriptives), writing a graded summary to <out-dir>/summary.json.

Apache-2.0. Standard library only.
    python job.py --data-dir /data --out-dir /out --allow-net
"""
from __future__ import annotations

import argparse
import datetime as dt
import http.client
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://bugs.openjdk.org/rest/api/2"
JQL = "issuetype = JEP ORDER BY key ASC"
FIELDS = "summary,status,created,resolution,resolutiondate,fixVersions,updated"
PAGE = 5
PAUSE = 2.0
UA = "MV2-Munim-research/1.0 (mv2@munimtech.com; jep-lifecycle-census)"
CACHE = "jep-jbs.json"

# JBS took over the JEP archive in June 2014; status events before this date are
# backfilled, so cohorts that use status dates start here.
CUTOFF = dt.date(2014, 7, 1)
CAND = {"Candidate", "Proposed to Target", "Targeted", "Integrated", "Completed"}
OPEN_EARLY = {"Draft", "Submitted"}
P1_OLD = (dt.date(2014, 7, 1), dt.date(2017, 8, 31))
P1_NEW = (dt.date(2018, 1, 1), dt.date(2023, 9, 30))
P2_WIN = (dt.date(2014, 7, 1), dt.date(2020, 12, 31))
P4_OLD = range(12, 18)
P4_NEW = range(22, 28)

ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
            "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11,
            "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15}
ROUND_RE = re.compile(r"\((?:([A-Za-z]+)\s+)?(Preview|Incubator)\)", re.I)


# ---------------------------------------------------------------- helpers

def parse_date(s):
    if not s:
        return None
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _name(v):
    if isinstance(v, dict):
        return v.get("name")
    return v


def _share(k, n):
    return None if n == 0 else k / n


def _jsonable(o):
    if isinstance(o, dt.date):
        return o.isoformat()
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(type(o).__name__)


def compact(issue):
    """Keep only what the study needs from one JBS issue."""
    f = issue.get("fields") or {}
    events = []
    cl = issue.get("changelog") or {}
    for h in cl.get("histories") or []:
        for it in h.get("items") or []:
            if it.get("field") in ("status", "resolution"):
                events.append([str(h.get("created", ""))[:10], it["field"], it.get("toString")])
    events.sort(key=lambda e: e[0])
    fixes = f.get("fixVersions") or []
    hist_n = len(cl.get("histories") or [])
    return {
        "key": issue.get("key"),
        "summary": f.get("summary") or "",
        "created": str(f.get("created") or "")[:10],
        "status": _name(f.get("status")),
        "resolution": _name(f.get("resolution")),
        "resolved": str(f.get("resolutiondate") or "")[:10] or None,
        "fix": [_name(v) for v in fixes],
        "fix_dates": {_name(v): v.get("releaseDate") for v in fixes if isinstance(v, dict)},
        "events": events,
        "truncated": bool(cl) and cl.get("total", hist_n) > hist_n,
    }


# ---------------------------------------------------------------- download

def get_json(url, tries=8):
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                wait = e.headers.get("Retry-After") if e.headers else None
                time.sleep(float(wait) if wait and wait.isdigit() else 30 * (i + 1))
                continue
            raise
        except (OSError, http.client.HTTPException, ValueError):
            if i < tries - 1:
                time.sleep(30 * (i + 1))
                continue
            raise


def download():
    recs, total, start, refetched = {}, None, 0, 0
    while total is None or start < total:
        q = urllib.parse.urlencode({"jql": JQL, "fields": FIELDS, "expand": "changelog",
                                    "startAt": start, "maxResults": PAGE})
        page = get_json(f"{API}/search?{q}")
        total = page.get("total", 0)
        issues = page.get("issues") or []
        if not issues:
            break
        for iss in issues:
            r = compact(iss)
            if r["truncated"]:
                time.sleep(PAUSE)
                full = get_json(f"{API}/issue/{iss['key']}?expand=changelog&fields={FIELDS}")
                r = compact(full)
                refetched += 1
            recs[r["key"]] = r
        start += len(issues)
        print(f"fetched {start}/{total}", file=sys.stderr, flush=True)
        time.sleep(PAUSE)
    return {"downloaded": dt.datetime.now(dt.timezone.utc).date().isoformat(),
            "total_reported": total, "refetched": refetched,
            "issues": sorted(recs.values(), key=lambda r: r["key"])}


def load(data_dir, allow_net):
    path = os.path.join(data_dir, CACHE)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    if not allow_net:
        sys.exit(f"no cache at {path} and --allow-net not given")
    blob = download()
    os.makedirs(data_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(blob, fh)
    return blob


# ---------------------------------------------------------------- per-JEP facts

def first_candidate(r):
    """Date of the first status change into Candidate or any later active state."""
    for d, field, to in r["events"]:
        if field == "status" and to in CAND:
            return parse_date(d)
    return None


def release_of(r):
    """Lowest all-digit fix version, e.g. '17' -> 17; None if there is none."""
    nums = [int(v) for v in r["fix"] if isinstance(v, str) and v.isdigit()]
    return min(nums) if nums else None


def round_of(summary):
    """('Preview'|'Incubator', ordinal) for a preview or incubator round, else None."""
    m = ROUND_RE.search(summary or "")
    if not m:
        return None
    word = (m.group(1) or "").lower()
    if word and word not in ORDINALS:
        return None
    return m.group(2).capitalize(), ORDINALS.get(word, 1)


def delivered_within(r, c0, days):
    if r["resolution"] != "Delivered":
        return False
    d = parse_date(r["resolved"])
    return d is not None and (d - c0).days <= days


# ---------------------------------------------------------------- predictions

def cand_cohort(recs, lo, hi):
    out = []
    for r in recs:
        c0 = first_candidate(r)
        if c0 is not None and lo <= c0 <= hi:
            out.append((r, c0))
    return out


def p1(recs):
    res = {}
    for name, (lo, hi) in (("old", P1_OLD), ("new", P1_NEW)):
        rows = cand_cohort(recs, lo, hi)
        k = sum(1 for r, c0 in rows if delivered_within(r, c0, 365))
        res[name] = {"window": [lo, hi], "n": len(rows), "delivered_1y": k,
                     "share": _share(k, len(rows))}
    return res


def p2(recs):
    rows = cand_cohort(recs, *P2_WIN)
    k = sum(1 for r, c0 in rows if not delivered_within(r, c0, 1826))
    by = {}
    for r, c0 in rows:
        if not delivered_within(r, c0, 1826):
            tag = r["resolution"] or ("open:" + str(r["status"]))
            by[tag] = by.get(tag, 0) + 1
    return {"window": list(P2_WIN), "n": len(rows), "not_delivered_5y": k,
            "share": _share(k, len(rows)), "by_outcome": dict(sorted(by.items()))}


def p3(recs, snapshot):
    rows = [r for r in recs if r["status"] in OPEN_EARLY and parse_date(r["created"])]
    old = [r for r in rows if (snapshot - parse_date(r["created"])).days > 1096]
    return {"n": len(rows), "older_than_3y": len(old), "share": _share(len(old), len(rows)),
            "by_status": {s: sum(1 for r in rows if r["status"] == s) for s in sorted(OPEN_EARLY)}}


def p4(recs):
    res = {}
    for name, rng in (("old", P4_OLD), ("new", P4_NEW)):
        rows = [r for r in recs if r["resolution"] == "Delivered" and release_of(r) in rng]
        k = sum(1 for r in rows if round_of(r["summary"]))
        res[name] = {"releases": [rng.start, rng.stop - 1], "n": len(rows), "rounds": k,
                     "share": _share(k, len(rows))}
    return res


def grade(m):
    g = {}
    o, n = m["P1"]["old"]["share"], m["P1"]["new"]["share"]
    g["P1"] = "NULL" if o is None or n is None else ("HELD" if n >= o + 0.20 else "FAILED")
    s = m["P2"]["share"]
    g["P2"] = "NULL" if s is None else ("HELD" if s >= 0.15 else "FAILED")
    s = m["P3"]["share"]
    g["P3"] = "NULL" if s is None else ("HELD" if s >= 0.50 else "FAILED")
    o, n = m["P4"]["old"]["share"], m["P4"]["new"]["share"]
    g["P4"] = "NULL" if o is None or n is None else ("HELD" if n >= o + 0.10 else "FAILED")
    return g


# ---------------------------------------------------------------- descriptives

def hist(values):
    out = {}
    for v in values:
        k = str(v)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def descriptives(recs, snapshot):
    delivered = [r for r in recs if r["resolution"] == "Delivered"]
    per_release = {}
    for r in delivered:
        rel = release_of(r)
        b = per_release.setdefault(str(rel), {"n": 0, "preview": 0, "incubator": 0, "max_round": 0})
        b["n"] += 1
        rd = round_of(r["summary"])
        if rd:
            b[rd[0].lower()] += 1
            b["max_round"] = max(b["max_round"], rd[1])
    lags = []
    for r in delivered:
        rel = release_of(r)
        ga = parse_date(r["fix_dates"].get(str(rel))) if rel is not None else None
        res = parse_date(r["resolved"])
        if ga and res:
            lags.append((res - ga).days)
    ptt = []
    for r in recs:
        prev = None
        for d, field, to in r["events"]:
            if field != "status":
                continue
            if to == "Proposed to Target":
                prev = parse_date(d)
            elif to == "Targeted" and prev is not None:
                ptt.append((parse_date(d) - prev).days)
                prev = None
    withdrawn_by_year = hist(parse_date(r["resolved"]).year for r in recs
                             if r["resolution"] == "Withdrawn" and parse_date(r["resolved"]))
    rounds = [round_of(r["summary"]) for r in delivered]
    return {
        "status_hist": hist(r["status"] for r in recs),
        "resolution_hist": hist(r["resolution"] for r in recs),
        "status_event_to_hist": hist(to for r in recs for _, f, to in r["events"] if f == "status"),
        "created_year_hist": hist(r["created"][:4] for r in recs if r["created"]),
        "first_candidate_year_hist": hist(c.year for c in (first_candidate(r) for r in recs) if c),
        "delivered_per_release": dict(sorted(per_release.items(),
                                             key=lambda kv: (len(kv[0]), kv[0]))),
        "delivered_round_ordinals": {
            "Preview": hist(x[1] for x in rounds if x and x[0] == "Preview"),
            "Incubator": hist(x[1] for x in rounds if x and x[0] == "Incubator")},
        "resolved_minus_ga_days": {"n": len(lags),
                                   "median": statistics.median(lags) if lags else None,
                                   "within_90": sum(1 for x in lags if -90 <= x <= 90)},
        "proposed_to_targeted_days": {"n": len(ptt),
                                      "median": statistics.median(ptt) if ptt else None,
                                      "max": max(ptt) if ptt else None},
        "withdrawn_by_year": withdrawn_by_year,
        "draft_submitted_oldest": sorted(
            ([r["key"], r["created"], r["summary"]] for r in recs if r["status"] in OPEN_EARLY),
            key=lambda x: x[1])[:15],
    }


def compute(recs, snapshot):
    return {"n_issues": len(recs),
            "n_truncated_changelogs": sum(1 for r in recs if r["truncated"]),
            "P1": p1(recs), "P2": p2(recs), "P3": p3(recs, snapshot), "P4": p4(recs),
            "descriptives": descriptives(recs, snapshot)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--allow-net", action="store_true")
    args = ap.parse_args()

    blob = load(args.data_dir, args.allow_net)
    snapshot = parse_date(blob.get("downloaded")) or dt.date.today()
    recs = blob["issues"]
    metrics = compute(recs, snapshot)
    verdicts = grade(metrics)
    summary = {"data_source": API + "/search?jql=" + JQL, "snapshot_date": snapshot,
               "total_reported": blob.get("total_reported"), "refetched": blob.get("refetched"),
               "metrics": metrics, "verdicts": verdicts}
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True, default=_jsonable)
    print(json.dumps({"verdicts": verdicts, "n_issues": len(recs),
                      "P1": metrics["P1"], "P2": metrics["P2"], "P3": metrics["P3"],
                      "P4": metrics["P4"]}, indent=2, sort_keys=True, default=_jsonable))


if __name__ == "__main__":
    main()
