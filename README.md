# jep-lifecycle-census

A pre-registered census of OpenJDK JDK Enhancement Proposals (JEPs) from the public JDK Bug
System: how long JEPs take from Candidate to delivery, how many never ship, how old the Draft
backlog is, and whether the six-month release cadence and preview/incubator rounds changed
what ships.

By MV2 of Munim, Inc. (mv2@munimtech.com). The work was made with AI agents working in his
name. Code: Apache-2.0. Results and text: CC BY 4.0.

## Results, run 1 (snapshot 2026-10-30, graded against PREREG.md)

All 563 JEP issues that JBS reported were read, with no truncated change logs. Three of the
four predictions held and one failed.

- **P1 HELD.** Of JEPs that first became Candidate between July 2014 and August 2017 (the
  JDK 9 years), 37.5% (45 of 120) were delivered within a year. Of those that became
  Candidate between January 2018 and September 2023 (the six-month cadence), 80.9% (110 of
  136) were. The rule needed a gap of at least 0.20; the gap is 0.43.
- **P2 FAILED.** The prediction was that at least 15% of JEPs that became Candidate from
  July 2014 to December 2020 would not be delivered within five years. Only 8.1% (17 of 211)
  were not: 8 withdrawn, 5 still Candidate, 3 marked Completed with no Delivered resolution
  and 1 Active. None was delivered late. Once a JEP reaches Candidate, it almost always ships.
- **P3 HELD.** Of the 68 JEPs now in Draft (60) or Submitted (8), 69.1% (47) were created
  more than three years ago. The oldest Draft dates from November 2011.
- **P4 HELD.** Preview and incubator rounds made up 25.7% (19 of 74) of the JEPs delivered in
  JDK 12 to 17 and 47.1% (40 of 85) of those delivered in JDK 22 to 27 (rule: at least 0.10
  higher; it is 0.21 higher).

Descriptives (no predictions): 18 of the 60 delivered preview-round JEPs were a third or
later round, although JEP 12 calls two rounds the norm. The longest delivered runs reach a
seventh preview and a twelfth incubator. A Proposed to Target JEP becomes Targeted after a
median of 11 days (353 cases, maximum 64). Withdrawals per year range from 1 to 11.

**A caveat that matters, and a follow-up.** Run 1 dates delivery by the JBS resolution date.
That date sits a median of 46 days before the release's GA date, and only 173 of 322
delivered JEPs with a release date are within 90 days of it. Follow-up 1 (`followup1/`,
pre-registered in `followup1/FOLLOWUP1.md` before it was run) re-grades P1 and P2 with
delivery dated by the GA date, tests two new predictions and publishes `jeps.csv`, one row
per JEP with its state dates.

Spot checks against live JBS on 2026-10-30: JEP 286 (resolved 2018-03-06, two weeks before
JDK 10's GA), the ten "Third Preview" JEPs (9 delivered, matching the run's count), and the
Draft and Submitted backlog (68 issues, 60 and 8, 47 created before 2023-10-29), all match.

Full numbers: `results/run1-summary.json`.

## Limits

JBS took over the JEP archive in June 2014, so cohorts by status date start then. Resolution
dates trail or lead the real release (see above). Rounds are read from titles only. Process
and Informational JEPs are included. Issues hidden from anonymous users are not counted. This
is a census of one project's records, not a judgment of any feature.

## Files

- `PREREG.md`: predictions P1-P4, definitions, grading rules (published before any data).
- `job.py`, `test_job.py`: the run-1 code and its hand-built fixture tests.
- `results/run1-summary.json`: the graded run-1 output.
- `followup1/`: pre-registration, code and tests for follow-up 1.

A note on the record: the first commit attempt (2026-10-30) was blocked by its own test gate.
One expected count in `test_job.py` was worked out wrong by hand (the fixture has six JEPs in
the P2 window, not five). Only that test line and its comments changed; `PREREG.md` and
`job.py` are unchanged from the version written before any data was read.

## Run it

    python -m unittest -v
    python job.py --data-dir ./data --out-dir ./out --allow-net
    python followup1/followup1.py --data-dir ./data --out-dir ./out-f1 --allow-net

Standard library only, Python 3.10 or newer.

Part of a series of lifecycle studies of standards and proposal processes by MV2 of Munim,
Inc.: IETF RFCs (rfc-obsolescence-survival, rfc-errata-hfdu-graveyard), Python PEPs
(pep-lifecycle-census), W3C specifications (w3c-spec-lifecycle) and Kubernetes feature gates
(k8s-feature-gate-census), all under github.com/munimtechnologies.

-- MV2, Munim, Inc.
