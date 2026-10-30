#!/usr/bin/env python3
"""OpenJDK JEP lifecycle census, follow-up 1.

Re-reads the run-1 JBS snapshot (jep-jbs.json in the same data volume) and computes the
pre-registered follow-up in FOLLOWUP1.md: S1 (P1 and P2 with delivery dated by the
release's GA date instead of the JBS resolution date), H1, H2, the resolution-to-GA lag
per release, and jeps.csv, one row per JEP issue with its state dates.

Apache-2.0. Standard library only.
    python followup1.py --data-dir /data --out-dir /out --allow-net
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import job as base  # noqa: E402  (run-1 job.py: loader, cohorts, round parser)

# GA dates of JDK feature releases (openjdk.org/projects/jdk/<N>/). Used only when JBS
# gives no releaseDate for the version; every disagreement with JBS is reported.
GA = {8: "2014-03-18", 9: "2017-09-21", 10: "2018-03-20", 11: "2018-09-25",
      12: "2019-03-19", 13: "2019-09-17", 14: "2020-03-17", 15: "2020-09-15",
      16: "2021-03-16", 17: "2021-09-14", 18: "2022-03-22", 19: "2022-09-20",
      20: "2023-03-21", 21: "2023-09-19", 22: "2024-03-19", 23: "2024-09-17",
      24: "2025-03-18", 25: "2025-09-16", 26: "2026-03-17", 27: "2026-09-15"}
JEP_RE = re.compile(r"^\s*JEP\s+(\d+)\s*:", re.I)
H1_WIN = (dt.date(2018, 1, 1), dt.date(2023, 9, 30))
TARGETED = {"Targeted", "Integrated", "Completed"}
COLS = ["key", "jep", "title", "created", "status", "resolution", "resolved", "release",
        "ga_date", "ga_source", "first_candidate", "first_proposed_to_target",
        "first_targeted", "first_integrated", "proposed_to_drop", "round_kind", "round_n"]


# ---------------------------------------------------------------- per-JEP facts

def _iso(d):
    return d.isoformat() if d else ""


def first_event(r, names, after=None):
    """Date of the first status change into one of `names` (on or after `after`)."""
    for d, field, to in r["events"]:
        if field == "status" and to in names:
            x = base.parse_date(d)
            if x is not None and (after is None or x >= after):
                return x
    return None


def ga_of(r):
    """(release, GA date, source) where source is 'jbs', 'table' or None."""
    rel = base.release_of(r)
    if rel is None:
        return None, None, None
    d = base.parse_date((r.get("fix_dates") or {}).get(str(rel)))
    if d is not None:
        return rel, d, "jbs"
    t = GA.get(rel)
    return rel, (dt.date.fromisoformat(t) if t else None), ("table" if t else None)


def delivery_date(r):
    """GA date of the release if known, else the resolution date."""
    rel, ga, src = ga_of(r)
    return ga if ga is not None else base.parse_date(r["resolved"])


def delivered_by(r, c0, days):
    if r["resolution"] != "Delivered":
        return False
    d = delivery_date(r)
    return d is not None and (d - c0).days <= days


# ---------------------------------------------------------------- follow-up statistics

def s1(recs):
    out = {}
    for name, (lo, hi) in (("old", base.P1_OLD), ("new", base.P1_NEW)):
        rows = base.cand_cohort(recs, lo, hi)
        k = sum(1 for r, c0 in rows if delivered_by(r, c0, 365))
        out["P1_" + name] = {"n": len(rows), "delivered_1y": k, "share": base._share(k, len(rows))}
    rows = base.cand_cohort(recs, *base.P2_WIN)
    k = sum(1 for r, c0 in rows if not delivered_by(r, c0, 1826))
    out["P2"] = {"n": len(rows), "not_delivered_5y": k, "share": base._share(k, len(rows))}
    o, n, s = out["P1_old"]["share"], out["P1_new"]["share"], out["P2"]["share"]
    out["verdicts"] = {
        "P1": "NULL" if o is None or n is None else ("HELD" if n >= o + 0.20 else "FAILED"),
        "P2": "NULL" if s is None else ("HELD" if s >= 0.15 else "FAILED")}
    return out


def h1(recs):
    days = []
    for r, c0 in base.cand_cohort(recs, *H1_WIN):
        if r["resolution"] != "Delivered":
            continue
        p = first_event(r, {"Proposed to Target"}, after=c0)
        if p is not None:
            days.append((p - c0).days)
    med = statistics.median(days) if days else None
    return {"n": len(days), "median_days": med, "over_365": sum(1 for x in days if x > 365),
            "verdict": "NULL" if med is None else ("HELD" if med <= 120 else "FAILED")}


def h2(recs):
    rows = [r for r in recs if r["resolution"] == "Withdrawn" and base.first_candidate(r)]
    hit = sorted(r["key"] for r in rows if first_event(r, TARGETED))
    share = base._share(len(hit), len(rows))
    return {"n": len(rows), "ever_targeted": len(hit), "share": share,
            "ever_targeted_keys": hit,
            "verdict": "NULL" if share is None else ("HELD" if share <= 0.25 else "FAILED")}


def ga_mismatches(recs):
    seen = {}
    for r in recs:
        for v, d in (r.get("fix_dates") or {}).items():
            if isinstance(v, str) and v.isdigit() and d and int(v) in GA:
                seen[int(v)] = d[:10]
    return {str(k): {"jbs": d, "table": GA[k]} for k, d in sorted(seen.items()) if d != GA[k]}


def lag_by_release(recs):
    by = {}
    for r in recs:
        if r["resolution"] != "Delivered":
            continue
        rel, ga, src = ga_of(r)
        res = base.parse_date(r["resolved"])
        if ga is not None and res is not None:
            by.setdefault(rel, []).append((res - ga).days)
    return {str(k): {"n": len(v), "median": statistics.median(v), "min": min(v), "max": max(v)}
            for k, v in sorted(by.items())}


def c0_to_delivery_by_year(recs):
    by = {}
    for r in recs:
        c0 = base.first_candidate(r)
        if c0 is None or c0 < base.CUTOFF or r["resolution"] != "Delivered":
            continue
        d = delivery_date(r)
        if d is not None:
            by.setdefault(c0.year, []).append((d - c0).days)
    return {str(y): {"n": len(v), "median": statistics.median(v),
                     "negative": sum(1 for x in v if x < 0)} for y, v in sorted(by.items())}


def row(r):
    m = JEP_RE.match(r["summary"] or "")
    rel, ga, src = ga_of(r)
    rd = base.round_of(r["summary"])
    return {"key": r["key"], "jep": m.group(1) if m else "", "title": r["summary"],
            "created": r["created"], "status": r["status"] or "",
            "resolution": r["resolution"] or "", "resolved": r["resolved"] or "",
            "release": "" if rel is None else rel, "ga_date": _iso(ga), "ga_source": src or "",
            "first_candidate": _iso(base.first_candidate(r)),
            "first_proposed_to_target": _iso(first_event(r, {"Proposed to Target"})),
            "first_targeted": _iso(first_event(r, {"Targeted"})),
            "first_integrated": _iso(first_event(r, {"Integrated"})),
            "proposed_to_drop": int(first_event(r, {"Proposed to Drop"}) is not None),
            "round_kind": rd[0] if rd else "", "round_n": rd[1] if rd else ""}


def compute(recs):
    delivered = [r for r in recs if r["resolution"] == "Delivered"]
    return {"S1": s1(recs), "H1": h1(recs), "H2": h2(recs),
            "ga_source_hist": base.hist(ga_of(r)[2] for r in delivered),
            "ga_mismatches": ga_mismatches(recs),
            "resolved_minus_ga_by_release": lag_by_release(recs),
            "c0_to_delivery_by_c0_year": c0_to_delivery_by_year(recs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--allow-net", action="store_true")
    args = ap.parse_args()

    blob = base.load(args.data_dir, args.allow_net)
    recs = blob["issues"]
    result = compute(recs)
    result.update({"snapshot_date": blob.get("downloaded"), "n_issues": len(recs)})
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True, default=base._jsonable)
    with open(os.path.join(args.out_dir, "jeps.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in sorted(recs, key=lambda r: r["key"]):
            w.writerow(row(r))
    print(json.dumps({k: result[k] for k in ("S1", "H1", "H2", "n_issues", "snapshot_date")},
                     indent=2, sort_keys=True, default=base._jsonable))


if __name__ == "__main__":
    main()
