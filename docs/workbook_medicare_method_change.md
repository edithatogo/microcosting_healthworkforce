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

The separate PSA scalar, mixed publication values, isolated zero, assumed units
and scientific/source applicability gaps retain their existing qualifications.
No numerical costing path or weighting formula is changed by this metadata fix.
