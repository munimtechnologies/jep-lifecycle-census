# Pre-registration: OpenJDK JEP lifecycle census, run 1

**By MV2 of Munim, Inc. Prepared with AI agents working in his name.**
**Filed: 2026-10-30 (UTC), before any JEP status history was downloaded or counted.**
Code: Apache-2.0. Text: CC BY 4.0.

## Question

How do JDK Enhancement Proposals (JEPs) move from Candidate to delivery, how many never
ship, how old is the Draft backlog, and did the move to a six-month release cadence (JDK 10,
March 2018) and the growth of preview and incubator rounds (JEP 12, JDK 12 onward) change the
mix of what ships?

## Data

Every issue of type JEP in the public JDK Bug System, read anonymously through its REST API
(`https://bugs.openjdk.org/rest/api/2/search?jql=issuetype = JEP`, with the change log), at
the date of the run. A spot query on 2026-10-30 reported 563 such issues. For each issue the
job keeps: key, title, created date, current status and resolution, resolution date, fix
versions (with their listed release dates), and every status and resolution change with its
date. Nothing else is stored. Change logs reported as incomplete are re-read one issue at a
time; any that stay incomplete are counted.

JBS took over the JEP archive in June 2014. The change logs of older JEPs show their states
set on migration day, so any cohort defined by a status date starts on 2014-07-01.

## Definitions

- **First Candidate date (c0):** the date of the first status change into Candidate, Proposed
  to Target, Targeted, Integrated or Completed.
- **Delivered:** current resolution "Delivered". **Delivery date:** the issue's resolution
  date. (The run reports how far resolution dates sit from the listed release dates.)
- **Release:** the lowest all-digit fix version (for example "17"); "tbd" and project names
  are ignored.
- **Preview or incubator round:** the title contains "(Preview)", "(Incubator)", or an
  English ordinal before either word, such as "(Third Preview)" or "(Tenth Incubator)".

## Predictions and rules

None of these is fully blind: the JEP index page (current status of each JEP) and well-known
release histories were seen before filing. No status dates had been counted.

**P1 (confirmatory: JDK 9 is known to have taken three years).** The share delivered within
365 days of c0 is at least 0.20 higher for c0 from 2018-01-01 to 2023-09-30 (six-month
cadence, all with a full year of follow-up) than for c0 from 2014-07-01 to 2017-08-31 (the
JDK 9 train). HELD if new >= old + 0.20, else FAILED.

**P2 (partly informed).** Of JEPs with c0 from 2014-07-01 to 2020-12-31, at least 15% were
not delivered within 1,826 days (5 years) of c0: withdrawn, still open, or delivered later.
HELD if the share is at least 0.15, else FAILED. The outcomes are broken down.

**P3 (partly informed: the index lists about 58 Draft and 8 Submitted JEPs).** Of JEP issues
whose current status is Draft or Submitted, at least half were created more than 1,096 days
(3 years) before the snapshot. HELD if the share is at least 0.50, else FAILED.

**P4 (partly informed).** Among delivered JEPs, the share that are preview or incubator
rounds is at least 0.10 higher for releases 22-27 than for releases 12-17. HELD if new >= old
+ 0.10, else FAILED.

## Descriptives (no predictions)

Current status, resolution and status-change histograms; JEPs created per year; first
Candidate dates per year; delivered JEPs per release with preview and incubator counts and the
highest round number; the round-number distribution (JEP 12 calls two rounds of previewing the
norm); days from resolution to the listed release date; days from Proposed to Target to
Targeted; withdrawals per year; and the 15 oldest Draft or Submitted JEPs.

## Limits

Resolution dates can trail the actual release. Some JEPs were renamed or merged, and title
matching for rounds reads only titles. Process and Informational JEPs are included (there are
only a handful). JEP 145 and 187 are known to have vanished from the public index; issues
not visible to anonymous users are not counted. This is a census of one project's records, not
a judgment of how well any feature was designed.

## Nearest prior work

Release write-ups and blogs tabulate preview rounds per language feature (for example the
howtodoinjava feature table); OpenJDK's draft JEP 8300604 ("Preview Features: A Look Back, and
A Look Ahead") discusses round counts in prose; chriswhocodes.com has a JEP map. Searches on
2026-10-30 found no study of JEP status-change timing, candidate-to-delivery rates or the
Draft backlog from JBS histories.
