# Historical aggregate DSA scenarios

The hash-bound workbook profile identifies the five unweighted `ALL` rows in
`Labour - Prices (DSA)` and names their input bounds, source reference
aggregates and ten one-at-a-time output axes. Each axis has three historical
annual-cost results and three hourly-cost results. The hours axis uses upper,
midpoint and lower denominators for its lower, midpoint and upper hourly cost
respectively; the other output axes use the midpoint-hours denominator.

The labels describe workbook formula structure. They do not establish that the
bounds are statistical intervals, that Medicare counts are workforce weights,
or that any value is an accepted condition. A blank lower annual-leave input
in the first aggregate row remains blank, and an isolated zero below the block
is not moved into it. Original formulas and values are preserved.

The first aggregate annual-leave lower formula, `CW34`, references the
blank `AK34` through `(52+AK34)/52`. The retained workbook
lacks the salary and result caches needed for a numerical replay.

A private LibreOffice recalculation kept AK34 blank and produced a
numeric CW34 result. An independent replay matched it using zero
for the blank operand, the only blank among the inputs to the 300
calculations. The AO34 multiplier applies to the final
annual-leave term only, before dividing the full sum by Q34.

The independent replay matched all 300 annual and hourly results
across the ten axes, three bounds and five aggregate rows. The largest
absolute difference was below AUD 0.000000001.
