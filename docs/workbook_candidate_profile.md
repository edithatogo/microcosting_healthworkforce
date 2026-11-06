# Historical workbook candidate profile

`src.workbook_profile.load_candidate_profile()` loads bundled metadata for the
retained workbook identified by its SHA-256. Pass the actual catalogue hash to
`profile.table_definitions(catalog.sha256)`, then pass those definitions and the
catalogue to `src.workbook_tables.extract_tables`. The extraction preserves each
populated cell and reports unassigned cells and empty sheets.

This profile contains candidate and unresolved physical sections. Its column
roles and units are historical interpretations requiring further review; the
profile does not accept a condition, choose an industrial instrument, evaluate a
formula, or make a stochastic result valid. A successful complete-cell inventory
is not complete semantic qualification. The workbook bytes are not bundled in the
profile metadata. A different workbook hash must be reviewed independently.
