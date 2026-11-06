# Historical workbook ALL component basis — 6 November 2026

In `Labour - Prices`, the five role rows 77–81 use the same pattern for eight
salary-based components: each formula takes an unweighted average of five
jurisdiction inputs and multiplies it by the midpoint salary in rows 4–8 of
the first jurisdiction. The annual-leave proxy additionally divides by 52.
All 40 formulas were checked exactly against this pattern. The salary bounds
shown in columns V–X instead average the five jurisdiction salaries.

This formula is not generally equal to the unweighted mean of the five
jurisdiction-specific component amounts, which multiply each input by its own
jurisdiction's midpoint salary. A bounded calculation from the workbook's own
inputs compared those alternatives for the 40 formulas: nine had zero in both
methods; all 31 nonzero comparisons differed, with the largest absolute
difference about 40.73% of the alternative mean. This is a comparison against a
possible alternative, not proof that an unweighted mean is the intended
aggregation or a replacement for the original formula. It also does not assess
the source assumptions or current entitlements.

The source file's cached midpoint formula results were unavailable. The
comparison independently recomputed the 25 midpoints after verifying each
midpoint formula; constant-only arithmetic in lower and upper salary cells was
evaluated with a restricted arithmetic parser. Preserve the original formulas,
the first-jurisdiction basis, and the alternative interpretation separately.
The overall candidate profile and economic interpretation remain unaccepted.
The reproducible private check and receipt are
`.private-runs/workbook-source-inventory/check-all-component-basis.py` and
`.private-runs/workbook-source-inventory/all-component-basis-v1.json`.
