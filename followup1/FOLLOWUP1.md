# Pre-registration: JEP lifecycle census, follow-up 1

**By MV2 of Munim, Inc. Prepared with AI agents working in his name.**
**Filed: 2026-10-30 (UTC), after run 1 was graded (results/run1-summary.json) and before
any of the statistics below were computed.** Code: Apache-2.0. Text: CC BY 4.0.

What had been seen when this was written: the run-1 summary only (P1-P4, the descriptives),
plus three live spot checks of JBS (JEP 286, the ten "Third Preview" JEPs, the Draft and
Submitted backlog). No per-JEP dates from the snapshot had been read.

## Why a follow-up

Run 1 dated delivery by the JBS resolution date. Its own descriptive shows that this date
sits a median of 46 days before the GA date of the release, and only 173 of 322 delivered
JEPs with a release date are within 90 days of it. So P1 and P2 are re-graded with delivery
dated by the release's GA date. The follow-up also publishes the per-JEP table.

## Data

The same snapshot as run 1 (jep-jbs.json, downloaded 2026-10-30, 563 JEP issues), read
from the same data volume. Nothing new is downloaded unless that file is missing.

## Definitions

- **GA date:** the JBS releaseDate of the JEP's release (lowest all-digit fix version). If
  JBS gives none, the GA date from the OpenJDK project page for that release (JDK 8 to 27,
  table in followup1.py). Every release where the table and JBS disagree is listed.
- **Delivery date (GA dating):** the GA date if known, else the resolution date.
- **c0:** as in run 1 (first status change into Candidate or any later active state).

## Sensitivity and predictions

**S1 (sensitivity, expectation stated).** P1 and P2 re-graded with GA dating and the run-1
rules unchanged. Expected: P1 stays HELD and P2 stays FAILED. If either verdict flips, the
run-1 verdict is reported as not robust to the delivery date.

**H1 (partly informed: run 1 showed 81% delivered within a year of c0 in this cohort).**
For delivered JEPs with c0 from 2018-01-01 to 2023-09-30, the median number of days from
c0 to the first Proposed to Target on or after c0 is at most 120. HELD if <= 120, else
FAILED.

**H2 (partly informed: run 1 counted only 5 Proposed to Drop events in all of JBS).** Of
withdrawn JEPs that ever reached Candidate, at most 25% had first reached Targeted,
Integrated or Completed (that is, were pulled after being targeted to a release). HELD if
the share is <= 0.25, else FAILED. The keys of those JEPs are listed.

## Descriptives (no predictions)

Resolution-to-GA lag per release (median, min, max); GA date sources (JBS or table); days
from c0 to delivery (GA dating) by c0 year; and jeps.csv: one row per JEP issue with its
key, JEP number, title, created date, current status and resolution, resolution date,
release, GA date and its source, the first Candidate, Proposed to Target, Targeted and
Integrated dates, whether it was ever Proposed to Drop, and its preview or incubator round.
No person's name or account is in the table.

## Limits

The same limits as run 1: JBS histories start in June 2014, titles are the only source for
rounds, and issues hidden from anonymous users are not counted. A GA date says when a release
shipped, not when every feature in it was finished.
