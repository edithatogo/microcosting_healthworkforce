# Repeat-recall payment exclusions

`partition_repeat_recalls` retains actual work and travel while applying an
explicitly selected payment-exclusion convention. It complements the recall
quantity and anchored-window methods; the methods represent different decisions.

A `RecallEpisode` supplies a distinct commencement clock, one allocation and
identified `RecallSegment` intervals (`work`, `outbound_travel`, `return_travel`).
The clock is an explicit input at or before the episode's first interval; it is
not inferred from arrival time, a phone contact or a paid guarantee. A complete
`RecallHistory` states the observation boundary and the latest earlier
commencement, or explicitly asserts none is relevant. Earlier work/travel must
already have ended by the observation boundary.

The selected `previous_commencement_half_open_v1` method uses the immediately
previous episode's commencement plus the supplied exclusion duration. Every
episode resets the clock, including one wholly excluded from payment. Actual
intervals before that cutoff are excluded; intervals straddling it are split
exactly. The cutoff instant is eligible. Midnight and daylight-saving changes
do not reset the elapsed-time clock.

The result retains every original interval, its first eligible instant (or an
explicit fully excluded result), excluded/eligible microseconds and the prior
clock. `next_history` carries the latest commencement and an observation
boundary at the end of all processed actual intervals. Reusing that history for
the next batch gives the same exclusions as processing the batches together.
Episodes must be sequential, including their commencement-to-final-segment
envelopes: interleaved episodes are rejected even when actual segments do not
overlap. Duplicate IDs/clocks, overlapping actual work/travel, missing history, naive or
nonpositive intervals and mismatched allocations fail explicitly.

For example, with a synthetic one-hour exclusion, a prior recall commencing at
10:00 and a repeat commencing at 10:50 can have outbound travel 10:50–10:55,
work 10:55–11:05 and return travel 11:05–11:10. The second episode retains all
20 actual minutes. Its outbound travel and first five working minutes are
excluded from payment; five working and five return-travel minutes remain
eligible. No two-hour minimum or travel cap is inferred from this calculation.

## Effective-dated eligible-time pricing

`cost_eligible_recalls(release, resource_id, plan)` rechecks the derived partition
against its original inputs and prices only eligible actual intervals through
`cost_dynamic`. The release supplies precomputed component rates and verified
source coverage, including any rate transition within an eligible interval.
The returned plan and ledger keep actual-time and monetary evidence together.
This uses the selected resource rate for both work and travel; another basis
requires a separately qualified method.

Excluded payment time remains actual work/travel evidence. It must not silently
be deleted from an overtime history. This method supplies neither an overtime
accumulator nor a decision that travel is worked overtime time.

## Source qualification and remaining interactions

The method, clock meaning, observation completeness and source applicability
are caller-qualified assumptions. This is not an automatic interpretation of an
industrial instrument. In particular, selecting immediately previous
commencement and resetting after a wholly excluded episode are explicit method
choices. Keep a different or unresolved source interpretation in the candidate
layer rather than silently substituting an anchored minimum window.

No source-derived exclusion duration is a library default. The method does not
resolve interaction with a minimum, rounding, travel caps, per-contact fees,
calendar premiums or employer approval. Applying the minimum after an exclusion
could restore excluded payment; applying the exclusion to an invented guaranteed
interval could suppress a different quantity. Neither is done implicitly here.
The separate quantity method is for independently eligible recalls; passing it
clipped durations would mislabel eligible time as original actual time. A
qualified composition must preserve both layers and define the order explicitly.
