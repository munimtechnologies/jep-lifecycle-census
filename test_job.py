"""Tests for job.py against a hand-built fixture. Apache-2.0.

Every expected number below was worked out by hand from the fixture (see the
comments), not by running job.py.
"""
import datetime as dt
import unittest

import job

SNAP = dt.date(2026, 10, 30)


def rec(key, summary, created, status, resolution=None, resolved=None, fix=(),
        fix_dates=None, events=()):
    return {"key": key, "summary": summary, "created": created, "status": status,
            "resolution": resolution, "resolved": resolved, "fix": list(fix),
            "fix_dates": dict(fix_dates or {}), "events": [list(e) for e in events],
            "truncated": False}


def S(d, to):
    return (d, "status", to)


FIXTURE = [
    # c0 2018-03-01 -> P1 new; delivered after 208 days. P2 delivered. PTT 7 days. Release 11.
    rec("JDK-1", "JEP 1: Foo (Second Preview)", "2018-01-10", "Closed", "Delivered",
        "2018-09-25", ["11"], {"11": "2018-09-25"},
        [S("2018-02-01", "Submitted"), S("2018-03-01", "Candidate"),
         S("2018-06-01", "Proposed to Target"), S("2018-06-08", "Targeted"),
         ("2018-09-25", "resolution", "Delivered"), S("2018-09-25", "Closed")]),
    # c0 2014-09-01 -> P1 old (not within 1y), P2 delivered within 5y (1,116 days).
    rec("JDK-2", "JEP 2: Bar", "2014-08-01", "Closed", "Delivered", "2017-09-21",
        ["9"], {"9": "2017-09-21"}, [S("2014-09-01", "Candidate"), S("2017-09-21", "Closed")]),
    # c0 2015-02-01 -> P1 old, P2 not delivered (Withdrawn).
    rec("JDK-3", "Baz", "2015-01-01", "Closed", "Withdrawn", "2019-05-05", [], {},
        [S("2015-02-01", "Candidate"), S("2019-05-05", "Closed")]),
    # c0 2019-06-01 -> P1 new, delivered after 290 days (2020 is a leap year); P2 delivered.
    # Release 14, an incubator round. PTT 9 days.
    rec("JDK-4", "JEP 4: Qux (Incubator)", "2019-01-01", "Closed", "Delivered", "2020-03-17",
        ["14"], {"14": "2020-03-17"},
        [S("2019-06-01", "Candidate"), S("2019-10-01", "Proposed to Target"),
         S("2019-10-10", "Targeted"), S("2020-03-17", "Closed")]),
    # c0 2021-03-01 -> P1 new, not within 1y; outside P2. Release 22, not a round.
    rec("JDK-5", "JEP 5: Quux", "2021-01-01", "Closed", "Delivered", "2024-03-19",
        ["22"], {"22": "2024-03-19"}, [S("2021-03-01", "Candidate"), S("2024-03-19", "Closed")]),
    # c0 2024-01-15 -> outside P1. Release 23, a third preview.
    rec("JDK-6", "JEP 6: Corge (Third Preview)", "2023-01-01", "Closed", "Delivered",
        "2024-09-17", ["23"], {"23": "2024-09-17"},
        [S("2024-01-15", "Candidate"), S("2024-09-17", "Closed")]),
    # Draft created 2020-05-05: older than 3 years at the snapshot.
    rec("JDK-7", "Draft thing", "2020-05-05", "Draft"),
    # Submitted, created 2025-01-01: younger than 3 years.
    rec("JDK-8", "Another draft", "2025-01-01", "Submitted",
        events=[S("2025-02-01", "Submitted")]),
    # c0 2016-03-01 -> P1 old, P2 not delivered (still open as Candidate).
    rec("JDK-9", "JEP 9: Grault", "2016-01-01", "Candidate",
        events=[S("2016-03-01", "Candidate")]),
    # Migration-day backfill (2014-06-10) -> in no cohort. Release 8.
    rec("JDK-10", "JEP 10: Old", "2011-01-01", "Closed", "Delivered", "2014-08-06", ["8"], {},
        [S("2014-06-10", "Completed"), S("2014-08-06", "Closed")]),
    # c0 2020-12-01 -> P1 new, delivered after 287 days; P2 delivered. Release 17, resolved
    # 6 days before the listed release date.
    rec("JDK-11", "JEP 11: Garply", "2016-05-01", "Closed", "Delivered", "2021-09-14",
        ["17"], {"17": "2021-09-20"}, [S("2020-12-01", "Candidate"), S("2021-09-14", "Closed")]),
]


class TestHelpers(unittest.TestCase):
    def test_round_of(self):
        self.assertEqual(job.round_of("Vector API (Tenth Incubator)"), ("Incubator", 10))
        self.assertEqual(job.round_of("JEP 325: Switch Expressions (Preview)"), ("Preview", 1))
        self.assertEqual(job.round_of("Pattern Matching for switch (Fourth Preview)"),
                         ("Preview", 4))
        self.assertIsNone(job.round_of("JEP 999: Something (Experimental)"))
        self.assertIsNone(job.round_of("JEP 998: Odd (Bogus Preview)"))
        self.assertIsNone(job.round_of("JEP 12: Preview Features"))

    def test_release_of(self):
        self.assertEqual(job.release_of({"fix": ["tbd", "21", "17"]}), 17)
        self.assertIsNone(job.release_of({"fix": ["repo-valhalla"]}))
        self.assertIsNone(job.release_of({"fix": []}))

    def test_first_candidate(self):
        self.assertEqual(job.first_candidate(FIXTURE[0]), dt.date(2018, 3, 1))
        self.assertEqual(job.first_candidate(FIXTURE[9]), dt.date(2014, 6, 10))
        self.assertIsNone(job.first_candidate(FIXTURE[6]))

    def test_compact(self):
        issue = {
            "key": "JDK-42",
            "fields": {"summary": "JEP 42: X", "created": "2019-01-02T03:04:05.000+0000",
                       "status": {"name": "Closed", "id": "6"},
                       "resolution": {"name": "Delivered"},
                       "resolutiondate": "2020-03-17T10:00:00.000+0000",
                       "fixVersions": [{"name": "14", "releaseDate": "2020-03-17"}]},
            "changelog": {"startAt": 0, "maxResults": 3, "total": 4, "histories": [
                {"created": "2019-06-01T00:00:00.000+0000",
                 "items": [{"field": "status", "fromString": "Draft", "toString": "Candidate"}]},
                {"created": "2019-01-03T00:00:00.000+0000",
                 "items": [{"field": "Link", "fromString": None, "toString": "x"},
                           {"field": "status", "fromString": "Submitted", "toString": "Draft"}]},
                {"created": "2020-03-17T10:00:00.000+0000",
                 "items": [{"field": "resolution", "toString": "Delivered"},
                           {"field": "status", "toString": "Closed"}]},
            ]},
        }
        r = job.compact(issue)
        self.assertEqual(r["created"], "2019-01-02")
        self.assertEqual(r["status"], "Closed")
        self.assertEqual(r["resolution"], "Delivered")
        self.assertEqual(r["resolved"], "2020-03-17")
        self.assertEqual(r["fix"], ["14"])
        self.assertEqual(r["fix_dates"], {"14": "2020-03-17"})
        self.assertEqual(r["events"], [["2019-01-03", "status", "Draft"],
                                       ["2019-06-01", "status", "Candidate"],
                                       ["2020-03-17", "resolution", "Delivered"],
                                       ["2020-03-17", "status", "Closed"]])
        self.assertTrue(r["truncated"])


class TestPredictions(unittest.TestCase):
    def setUp(self):
        self.m = job.compute(FIXTURE, SNAP)

    def test_p1(self):
        p = self.m["P1"]
        self.assertEqual((p["old"]["n"], p["old"]["delivered_1y"]), (3, 0))
        self.assertEqual(p["old"]["share"], 0.0)
        self.assertEqual((p["new"]["n"], p["new"]["delivered_1y"]), (4, 3))
        self.assertAlmostEqual(p["new"]["share"], 0.75)

    def test_p2(self):
        # c0 from 2014-07-01 to 2020-12-31: JDK-1, 2, 3, 4, 9 and 11 (six JEPs); JDK-3
        # (withdrawn) and JDK-9 (still a Candidate) were not delivered within 5 years.
        p = self.m["P2"]
        self.assertEqual((p["n"], p["not_delivered_5y"]), (6, 2))
        self.assertAlmostEqual(p["share"], 2 / 6)
        self.assertEqual(p["by_outcome"], {"Withdrawn": 1, "open:Candidate": 1})

    def test_p3(self):
        p = self.m["P3"]
        self.assertEqual((p["n"], p["older_than_3y"]), (2, 1))
        self.assertAlmostEqual(p["share"], 0.5)
        self.assertEqual(p["by_status"], {"Draft": 1, "Submitted": 1})

    def test_p4(self):
        p = self.m["P4"]
        self.assertEqual((p["old"]["n"], p["old"]["rounds"]), (2, 1))
        self.assertEqual((p["new"]["n"], p["new"]["rounds"]), (2, 1))

    def test_grades(self):
        self.assertEqual(job.grade(self.m),
                         {"P1": "HELD", "P2": "HELD", "P3": "HELD", "P4": "FAILED"})

    def test_grade_nulls(self):
        m = job.compute([], SNAP)
        self.assertEqual(set(job.grade(m).values()), {"NULL"})


class TestDescriptives(unittest.TestCase):
    def setUp(self):
        self.d = job.compute(FIXTURE, SNAP)["descriptives"]

    def test_proposed_to_targeted(self):
        self.assertEqual(self.d["proposed_to_targeted_days"], {"n": 2, "median": 8.0, "max": 9})

    def test_round_ordinals(self):
        self.assertEqual(self.d["delivered_round_ordinals"],
                         {"Preview": {"2": 1, "3": 1}, "Incubator": {"1": 1}})

    def test_resolved_minus_ga(self):
        self.assertEqual(self.d["resolved_minus_ga_days"], {"n": 6, "median": 0.0, "within_90": 6})

    def test_per_release_and_withdrawn(self):
        self.assertEqual(self.d["delivered_per_release"]["11"],
                         {"n": 1, "preview": 1, "incubator": 0, "max_round": 2})
        self.assertEqual(self.d["withdrawn_by_year"], {"2019": 1})
        self.assertEqual(self.d["status_hist"]["Closed"], 8)


if __name__ == "__main__":
    unittest.main()
