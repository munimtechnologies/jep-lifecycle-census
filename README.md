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

Run 1 dated delivery by the JBS resolution date, which sits a median of 46 days before the
release's GA date. Follow-up 1 re-grades with the GA date.

## Results, follow-up 1 (same snapshot, graded against followup1/FOLLOWUP1.md)

Pre-registered on 2026-10-30 (UTC) after run 1 was graded; run once on 2026-10-31 in a sealed
container (tests passed first). All 563 JEP issues were read again. Every verdict held.

- **S1 (sensitivity): both run-1 verdicts are robust to the delivery date.** With delivery
  dated by the release's GA date, P1 still HELD: 17.5% (21 of 120) of 2014-2017 Candidates
  were delivered within a year, against 79.4% (108 of 136) of 2018-2023 Candidates. The gap
  grew from 0.43 to 0.62, mostly because the early cohort shipped in JDK 9, whose JEPs were
  resolved a median of 196 days before its long-delayed GA. P2 still FAILED: 8.1% (17 of 211), unchanged.
- **H1 HELD.** For delivered JEPs that became Candidate from 2018 to September 2023, the median
  time from Candidate to the first Proposed to Target was 36.5 days (126 JEPs; rule: at most
  120). 8 of them waited over a year.
- **H2 HELD.** Of 20 withdrawn JEPs that had reached Candidate, 2 (10%) had been targeted to a
  release before they were pulled (rule: at most 25%): JEP 198 (Light-Weight JSON API) and
  JEP 326 (Raw String Literals, Preview). Both were checked against live JBS on 2026-10-31
  (Closed, Withdrawn, no fix version). Almost every withdrawal happens before targeting.

How blind: S1 had a stated expectation, and H1 and H2 were partly informed by run 1 (labelled
in FOLLOWUP1.md).

Descriptives (no predictions):
- **GA dates:** 322 rows took the GA date from JBS and 52 from the OpenJDK release table in
  `followup1.py`; 17 had neither. Where both sources gave a date, they never disagreed.
- **Resolution date minus GA date, by release:** JDK 8's JEPs were resolved a median of 411
  days AFTER GA (JBS took over the JEP records in mid-2014, after JDK 8 shipped). JDK 9's were
  resolved a median of 196 days before GA. From JDK 10 to JDK 27 the per-release median runs
  from 13 to 65 days before GA.
- **Candidate to delivery (GA dating), median days by Candidate year:** 1,047 (2014), 779.5
  (2015), 516 (2016), 278 (2017), then 154 to 195 for every year from 2018 to 2026. The
  latest years count only JEPs already delivered, so they are biased low.

`results/jeps.csv` has one row per JEP issue: key, number, title, created date, status,
resolution, resolution date, release, GA date and its source, first Candidate, Proposed to
Target, Targeted and Integrated dates, whether it was ever Proposed to Drop, and its preview or
incubator round. No person's name or account is in it.

## Limits

JBS took over the JEP archive in June 2014, so cohorts by status date start then. Rounds are
read from titles only. Process and Informational JEPs are included. Issues hidden from
anonymous users are not counted. A GA date says when a release shipped, not when each
feature in it was finished. This is a census of one project's records, not a judgment of any
feature.

## Files

- `PREREG.md`: predictions P1-P4, definitions, grading rules (published before any data).
- `job.py`, `test_job.py`: the run-1 code and its hand-built fixture tests.
- `results/run1-summary.json`: the graded run-1 output.
- `followup1/`: pre-registration (`FOLLOWUP1.md`), code and tests for follow-up 1.
- `results/followup1-summary.json`, `results/jeps.csv`: the graded follow-up 1 output.

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
(pep-lifecycle-census), W3C specifications (w3c-spec-lifecycle), Kubernetes feature gates
(k8s-feature-gate-census) and Kubernetes KEP records (kep-record-audit), all under
github.com/munimtechnologies.

-- MV2, Munim, Inc.
