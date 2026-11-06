# Retrospective source boundary — 6 November 2026

The retained [ACT Support Services agreement edition](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0011/2519948/ACTPS-Support-Services-EA-2023-2026.pdf)
records original agreement operation from 26 January 2024, while clause C2.2.2
(PDF page 51) describes an increase from the first full pay period on or after
1 June 2023. This date sequence requires a specific legal/source review; it does
not alone establish an individual backpay entitlement or explain how earlier
rates were applied. The edition includes later variation material, so the
source edition and knowledge date also matter.

The current `SourceRegistry.require_applicable` requires a source's operative
coverage on the date being tested. `first_full_period` checks source coverage
both on its trigger and the selected period start. A synthetic test using a
source operative from January 2024, a June 2023 trigger and complete June
boundaries correctly failed closed with `No verified source coverage for the
requested scope and date`. Thus the current method cannot express a later
instrument as reviewed evidence for an earlier entitlement date, even when a
specific retrospective effect is established. The release-history PR separates
knowledge-dated snapshots, but does not by itself change this source-coverage
boundary.

A complete implementation needs separate, explicitly sourced fields for the
source's own operative/knowledge dates and any independently reviewed
retrospective entitlement interval, plus pay-period and worker scope. Frozen
runs must not acquire later knowledge silently. Backpay and cash timing are
separate outputs. The ordinary source-coverage check must continue to reject
unreviewed extrapolation; merely changing a source's operative date to the
historical trigger would misstate the evidence. Record the unresolved legal
interpretation and any actual payroll boundaries before admitting a candidate.
