"""Hand-checked fixture tests for followup1.py. Apache-2.0.

Window membership of every fixture JEP (c0 = first Candidate-or-later status date):
  A c0 2018-03-01: P1 old no, P1 new YES, P2 YES, H1 YES
  B c0 2021-02-01: P1 old no, P1 new YES, P2 no,  H1 YES
  C c0 2015-01-05: P1 old YES, P1 new no, P2 YES, H1 no
  D c0 2014-08-01: P1 old YES, P1 new no, P2 YES, H1 no
  E no c0 (Draft only)
  F c0 2019-03-01: P1 old no, P1 new YES, P2 YES, H1 YES
Day counts (worked by hand):
  A: c0 -> PTT 2018-05-30 = 31+30+29 = 90; c0 -> resolved 2019-02-01 = 365-28 = 337;
     c0 -> GA 2019-03-19 = 365+18 = 383; resolved - GA = -(28+18) = -46
  B: c0 = PTT -> 0; c0 -> resolved 2021-08-20 = 181+19 = 200;
     c0 -> GA 2021-09-14 (table, no JBS date) = 212+13 = 225; resolved - GA = -(11+14) = -25
  D: c0 -> GA 2017-09-21 = 1096 (2016 leap) + 31 + 20 = 1147; resolved 2017-07-20 - GA = -63
"""
import unittest

import followup1 as f  # first: it puts the parent folder (run-1 job.py) on sys.path
import job as base


def rec(key, summary, status, resolution, resolved, fix, fix_dates, events):
    return {"key": key, "summary": summary, "created": "2014-01-01", "status": status,
            "resolution": resolution, "resolved": resolved, "fix": fix,
            "fix_dates": fix_dates, "events": [list(e) for e in events], "truncated": False}


A = rec("JDK-901", "JEP 901: Alpha", "Closed", "Delivered", "2019-02-01", ["12"],
        {"12": "2019-03-19"},
        [("2018-03-01", "status", "Candidate"), ("2018-05-30", "status", "Proposed to Target"),
         ("2018-06-10", "status", "Targeted"), ("2019-02-01", "resolution", "Delivered")])
B = rec("JDK-902", "JEP 902: Beta (Second Preview)", "Closed", "Delivered", "2021-08-20",
        ["17"], {"17": None},
        [("2021-01-10", "status", "Submitted"), ("2021-02-01", "status", "Proposed to Target"),
         ("2021-02-15", "status", "Targeted"), ("2021-08-20", "resolution", "Delivered")])
C = rec("JDK-903", "JEP 903: Gamma", "Closed", "Withdrawn", "2016-05-01", [], {},
        [("2015-01-05", "status", "Candidate"), ("2015-06-01", "status", "Targeted"),
         ("2015-09-01", "status", "Proposed to Drop"), ("2016-05-01", "resolution", "Withdrawn")])
D = rec("JDK-904", "JEP 904: Delta", "Closed", "Delivered", "2017-07-20", ["9"],
        {"9": "2017-09-21"},
        [("2014-08-01", "status", "Candidate"), ("2017-07-20", "resolution", "Delivered")])
E = rec("JDK-905", "Some draft", "Draft", None, None, [], {},
        [("2019-01-01", "status", "Draft")])
F = rec("JDK-906", "JEP 906: Epsilon", "Closed", "Withdrawn", "2020-01-01", [], {},
        [("2019-03-01", "status", "Candidate"), ("2020-01-01", "resolution", "Withdrawn")])
RECS = [A, B, C, D, E, F]


class TestFollowup1(unittest.TestCase):
    def test_s1_ga_dating(self):
        s = f.s1(RECS)
        self.assertEqual((s["P1_old"]["n"], s["P1_old"]["delivered_1y"]), (2, 0))
        self.assertEqual((s["P1_new"]["n"], s["P1_new"]["delivered_1y"]), (3, 1))
        self.assertAlmostEqual(s["P1_new"]["share"], 1 / 3)
        self.assertEqual((s["P2"]["n"], s["P2"]["not_delivered_5y"]), (4, 2))
        self.assertEqual(s["verdicts"], {"P1": "HELD", "P2": "HELD"})

    def test_resolution_dating_differs(self):
        # Run-1 rule (resolution date) counts A as delivered within a year; GA dating does not.
        self.assertEqual(base.p1(RECS)["new"]["delivered_1y"], 2)

    def test_h1(self):
        h = f.h1(RECS)
        self.assertEqual(h["n"], 2)
        self.assertEqual(h["median_days"], 45)
        self.assertEqual(h["over_365"], 0)
        self.assertEqual(h["verdict"], "HELD")

    def test_h2(self):
        h = f.h2(RECS)
        self.assertEqual((h["n"], h["ever_targeted"]), (2, 1))
        self.assertEqual(h["ever_targeted_keys"], ["JDK-903"])
        self.assertEqual(h["verdict"], "FAILED")

    def test_ga_sources_and_lags(self):
        self.assertEqual(f.ga_of(B)[1:], (base.parse_date("2021-09-14"), "table"))
        self.assertEqual(f.compute(RECS)["ga_source_hist"], {"jbs": 2, "table": 1})
        lag = f.lag_by_release(RECS)
        self.assertEqual(sorted(lag), ["12", "17", "9"])
        self.assertEqual((lag["9"]["median"], lag["12"]["median"], lag["17"]["median"]),
                         (-63, -46, -25))

    def test_c0_to_delivery(self):
        by = f.c0_to_delivery_by_year(RECS)
        self.assertEqual({y: v["median"] for y, v in by.items()},
                         {"2014": 1147, "2018": 383, "2021": 225})
        self.assertEqual(sum(v["negative"] for v in by.values()), 0)

    def test_ga_mismatches(self):
        self.assertEqual(f.ga_mismatches(RECS), {})
        self.assertEqual(f.ga_mismatches([{"fix_dates": {"10": "2018-03-21"}}]),
                         {"10": {"jbs": "2018-03-21", "table": "2018-03-20"}})

    def test_rows(self):
        a, b, c, e = f.row(A), f.row(B), f.row(C), f.row(E)
        self.assertEqual((a["jep"], a["release"], a["ga_date"], a["ga_source"]),
                         ("901", 12, "2019-03-19", "jbs"))
        self.assertEqual((a["first_proposed_to_target"], a["first_targeted"],
                          a["proposed_to_drop"]), ("2018-05-30", "2018-06-10", 0))
        self.assertEqual((b["round_kind"], b["round_n"], b["first_candidate"]),
                         ("Preview", 2, "2021-02-01"))
        self.assertEqual((c["proposed_to_drop"], c["release"]), (1, ""))
        self.assertEqual((e["jep"], e["release"], e["first_candidate"]), ("", "", ""))
        self.assertEqual(sorted(a), sorted(f.COLS))


if __name__ == "__main__":
    unittest.main()
