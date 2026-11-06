# Victorian scientist workbook source reconciliation — 6 November 2026

The [VHIA salary circular 770](https://www.vhia.com.au/wp-content/uploads/Circ-770-2.pdf)
identifies the 2017–2021 Victorian public health sector medical scientists,
pharmacists and psychologists agreement. The privately retained PDF has SHA-256
`226bdbd1d5b8955b6b98a8db9f89cfc4a28a07047f46ea1e9af28b7e81af93da`.
Its pages 17–18 were rendered and inspected. In the column for the first full
pay period on or after 25 January 2020, RX1 is $1,131.30 per week, RX4 is
$1,403.10, and RZ7 is $2,622.00. The circular includes later award-undertaking
updates for particular other classifications; those footnotes should not be
applied to the ordinary RX rows without evidence.

In `Labour - Prices` row 5, source note G5 explicitly names RX1–RZ7 and H5
records $1,131.30–$2,622.00: the two historical endpoints match the circular.
The grade label E5 instead states RX4–RZ7. The workbook's base year I5 is 2023;
its formulas V5 and X5 use weekly figures $1,177 and $2,741.40 annualised by 52.
The previously inspected 2021–2025 agreement's December 2022 schedule matched
those later figures to RX1 and RZ7 respectively. Thus the source note, historical
range and later formulas consistently identify RX1 at the lower end, while the
grade label identifies RX4. This is evidence of a real internal conflict, not
authority to decide which range the workbook author intended.

The circular is a secondary salary summary, not an independent determination of
a particular employee's agreement coverage. The workbook does not identify an
employer, individual grade or first-full-pay-period calendar. Do not replace
workbook cells, adopt RX1 or RX4 as an entitlement, or claim current coverage on
this evidence alone. Check employer, classification and relevant agreement chain
before creating an accepted source-backed condition. Original source bytes and
page renders remain private; a structured candidate record with source hash,
page, grade and workbook-cell lineage is retained in
`.private-runs/workforce-source-coverage-20261106/vic-vhia-770-workbook-row5-review.json`.
A public listing does not itself establish redistribution rights.
