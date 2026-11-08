# Historical Medicare method-change counts

The pinned original workbook's `Medicare Enrolments!A28` describes a change in
how estimated eligible persons were counted and distributed across jurisdictions.
The immediately following `A29:B37` table reports the signed jurisdictional
changes for September 2005. Both the full candidate profile and the focused
weight mapping therefore label its eight observations as:

- Column name: `eligible_persons_method_change`.
- Unit: `persons`.
- Role: `historical_method_change`.
- Table status: `archived_candidate`.

The header retains no numeric unit. Original labels, values, number formats and
formula text remain unchanged. The mapping is bound to the exact reviewed
workbook hash; it is not a heuristic inferred from whether numbers look like
counts. Negative changes remain signed counts, not invalid population weights.

This resolves the column's workbook-context unit and purpose. It does not verify
the historical figures against their original external publication, establish
population growth, or make the values eligible for current costing or workforce
weighting. The neighbouring card counts, persons counts, persons-per-card ratios
and selected five-state weight formulas retain their different meanings.

The separate PSA scalar, mixed publication values, isolated zero
and scientific and source applicability gaps retain their existing qualifications.
No numerical costing path or weighting formula is changed by this metadata fix.

An independent replay against the private recalculation matched all 17
outputs in the Weightings sheet's two five-state normalisations. Column D
uses the column C subtotal at C10, while column H uses the sum of G2:G6.
H7 checks the latter weights sum to one. These calculations establish
the workbook's selected-state denominators. Workforce representativeness
still requires separate evidence.

All ten weighted labour outputs in Z46:Z50 and AC46:AC50 on
`Labour - Prices (WM)` use the column H weights. Independent weighted
sums reproduced the annual and hourly results within 0.00000001.
The formula scan found 50 references to column H and none to column D.
