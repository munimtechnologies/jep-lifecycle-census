# jep-lifecycle-census

A pre-registered census of OpenJDK JDK Enhancement Proposals (JEPs) from the public JDK Bug
System: how long JEPs take from Candidate to delivery, how many never ship, how old the Draft
backlog is, and whether the six-month release cadence and preview/incubator rounds changed
what ships.

By MV2 of Munim, Inc. (mv2@munimtech.com). The work was made with AI agents working in his
name. Code: Apache-2.0. Results and text: CC BY 4.0.

## Status

`PREREG.md` (predictions P1-P4, definitions, grading rules) is published here before any
status history is downloaded or counted. `job.py` reads every JEP issue and its status
changes from the JBS REST API (anonymous, polite pace) and computes the statistics.
`test_job.py` checks the arithmetic against a hand-built fixture. Results will be added under
`results/` after one run in a sealed container.

A note on the record: the first commit attempt (2026-10-30) was blocked by its own test gate.
One expected count in `test_job.py` was worked out wrong by hand (the fixture has six JEPs in
the P2 window, not five). Only that test line and its comments changed; `PREREG.md` and
`job.py` are unchanged from the version written before any data was read.

## Run it

    python -m unittest -v
    python job.py --data-dir ./data --out-dir ./out --allow-net

Standard library only, Python 3.10 or newer.

Part of a series of lifecycle studies of standards and proposal processes by MV2 of Munim,
Inc.: IETF RFCs (rfc-obsolescence-survival, rfc-errata-hfdu-graveyard), Python PEPs
(pep-lifecycle-census) and W3C specifications (w3c-spec-lifecycle), all under
github.com/munimtechnologies.

-- MV2, Munim, Inc.
