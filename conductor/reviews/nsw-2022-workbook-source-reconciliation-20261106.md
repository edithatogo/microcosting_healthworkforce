# NSW 2022 workbook source reconciliation — 6 November 2026

The previously timed-out 4 November 2022 gazette is held through the
[NSW Industrial Relations Commission mirror](https://irc.nsw.gov.au/documents/industrial-gazette/2022/041122ig.pdf).
The retained 326-page PDF SHA-256 is
`08f4491b6c71d003144195b5ca99e11cc235a1dd7e9eb559e6e73e5791951334`;
the earlier failed retrieval remains recorded separately. Salary table pages
were rendered and checked against the text and column header.

`Labour - Prices` row 16 identifies a laboratory technician, labels the range
“Tech Assistant G1-3” and annualises $1,154.19 and $1,831.87 per week. The
2022 Health Employees Technical award's table has those amounts in its column
for the first full pay period on or after 1 July 2022: Technical Officer Grade 1
year 1 (PDF page 109) and Senior Technical Officer year 3 (page 110). The
latter figure also occurs under another technical classification, so amount
matching alone does not establish the author's intended classification. The
award's coverage includes NSW Health Service employees in its classifications
and excludes the County of Yancowinna. Neither the shorthand “Tech Assistant
G1-3” nor an individual employee's appointment is resolved by the amounts.

Row 17 annualises $1,292.77 and $2,664.91 per week and refers to the Hospital
Scientists award. The gazette's 2022 Health Professional and Medical Salaries
award lists those figures for Hospital Scientist year 1 and Senior or Chief
Hospital Scientist year 8 respectively (PDF page 140), effective from the first
full pay period on or after 1 July 2022. Its column header and coverage appear
on page 132. The same gazette's Hospital Scientists award clause 2 refers to
the salary award as varied or replaced; the two instruments must be considered
together. Several classifications share identical amounts, and the workbook's
“1-3” label does not identify a particular appointment or year of service.

These findings resolve historical holding and identify exact candidate salary
sources for two rows. They do not prove the workbook author's source, employer,
classification, first-full-pay-period date, present-day rate, or other
conditions. Retain both rows as historical candidates and do not promote them
to an accepted individual condition release. The structured private record
`nsw-2022-workbook-classification-review.json` retains cell, page, hash, scope
and source lineage; original workbook bytes were unchanged. Source reuse rights
remain unassessed.

## Bioinformatics candidate and date mismatch

`Labour - Prices` row 19 labels the role bioinformatics, cites the Hospital
Scientists award, gives the year as 2022 and uses literal annual salary endpoints
$66,106 and $114,763. An adjacent table in the same gazette's 2022 salary award
(PDF page 133, column header page 132) provides a plausible *numeric* match under
“Analyst, Chemist, Microbiologist, & Scientific Officer” for transferred Division
of Analytical Laboratories staff, grades 1–3. In that table, $66,106 is Grade 1
year 1 in the 2021 rate column; its corresponding 2022 rate is $67,778. The
$114,763 figure is Grade 3 year 3 in the 2022 rate column; its 2021 counterpart
is $111,931. Thus these two values match different dated columns under this
candidate interpretation.

This is not proof that the author used that table: $66,106 also appears for other
classifications. Nor does the transferred-staff table establish coverage for
bioinformaticians generally, or that the 2022 salary-column start applied at a
particular employer on a particular date. Preserve the original literals, record
the date/qualification ambiguity, and obtain the actual worker classification,
source and pay-period evidence before selecting conditions. The private
`nsw-2022-bioinformatics-candidate-review.json` records page and cell lineage.
A search of the same gazette's extracted text did not find the NSW administration
row's exact weekly endpoints; that is not a finding that no matching source exists.

## Administration and staff-specialist candidates

The [20 October 2022 gazette](https://irc.nsw.gov.au/documents/industrial-gazette/2022/201022ig.pdf)
contains the Health Employees Administrative Staff (State) Award 2022.
Its PDF pages 16–17 identify Administration Officer Level 1 year 1 at $926.56
per week *before* the first full pay period on or after 1 July 2022, and Level 4
year 2 at $1,302.02 *from* that pay period. These match the annualised endpoint
formulas in `Labour - Prices!V18` and `X18`, respectively. For comparison the
other column gives $950.00 and $1,269.89 for the respective classifications.
The source and grade cells for this workbook row are blank, and another general
administrative award also exists. This is a plausible historical numeric match,
not proof of the original source or a particular employee's coverage. The award
applies to its listed NSW Health Service classifications and excludes the County
of Yancowinna; individual appointment and pay-period timing remain necessary.

The [16 August 2022 gazette](https://irc.nsw.gov.au/documents/industrial-gazette/2022/160822ig.pdf)
contains the Staff Specialists (State) Award 2022. On PDF page 39, Schedule 1
shows $179,078 for Staff Specialist 1, $220,986 for Staff Specialist 5, and
$241,940 for Senior Staff Specialist. These are annual rates from the first full
pay period on or after 1 July 2022. `Labour - Prices` row 20 names that award and
labels the range SS1–SS5, but its upper endpoint is $241,940, the separate Senior
rate rather than SS5. The label/value discrepancy requires author intent and
individual classification evidence; it must not be silently corrected.

The two source PDFs, hashes, inspected page renders and structured candidate
records are retained privately in `nsw-2022-admin-specialist-review.json` and
its sibling files. The original workbook is unchanged; redistribution rights and
individual source applicability remain unassessed.

## Hospital scientist ordinary hours

The 2022 Hospital Scientists award in the recovered gazette, clause 4(i)–(ii)
(PDF page 156), states 152 ordinary hours over 28 calendar days for day workers
and no more than an average 38 ordinary hours per week per roster cycle for
shift workers, excluding meal times. The day-worker figure averages 38 hours
per week; this does not mean every week or every paid hour is identical.
`Labour - Prices!K17` records 38 for the medical-scientist row, consistent with
that average. The bioinformatics row `K19` records 40 while also citing the
Hospital Scientists award. If that award and ordinary-hours measure were intended
for that worker, the values differ; the workbook does not establish the role's
award coverage, roster or whether its 40-hour input represents a different
measure. Preserve both values and resolve that basis before accepting a rate.

This comparison concerns the 2022 edition; it does not determine the later 2025
award's separate employer-notice implementation condition. The private
`nsw-2022-scientist-hours-review.json` retains the source hash, clause, page and
workbook coordinates. The original workbook was not modified.

## Technical and administrative ordinary hours

Clause 4 of both the 2022 Technical award and Administrative Staff award
incorporates the Health Employees Conditions of Employment award as varied or
replaced. The 2022 conditions award, clause 3(ii)–(iii), specifies an average
38 ordinary hours per roster-cycle week for day workers and at most that average
for shift workers, excluding meals. Its clause 3 also contains classification
exceptions and a mechanism for agreed variation. The relevant incorporation and
hours pages were visually checked in the two gazettes.

The NSW laboratory and administration workbook rows `K16` and `K18` both use
40 hours per week. The salary-table matches identify plausible instruments but
do not prove that those instruments or the ordinary-hours measure apply to the
workbook's hypothetical workers. In particular, 40 rostered hours in one week
cannot simply be equated with a 28-day ordinary-hours average. Retain 40 in the
original, and establish appointment, roster cycle, any permitted variation and
the intended denominator before selecting a source-backed condition. The
private `nsw-2022-technical-admin-hours-review.json` records both award hashes,
clause and page references, and workbook coordinates.

## Consequence of the hours assumption

For rows 16, 18 and 19, all nine hourly output formulas in columns AB–AD divide
the corresponding annual cost by 52 and the row's column K value. A read-only
formula trace verified those nine exact references and confirmed all three K
values are 40. If the same annual cost were divided by 38 rather than 40, the
hourly output would be multiplied by 40/38 (20/19), an increase of approximately
5.26%. This is a one-variable arithmetic sensitivity, not a recalculated award
cost, an instruction to change the workbook or evidence that 38 is the right
input for the hypothetical workers. The denominator basis and source
applicability still require resolution. The private
`nsw-hours-denominator-effects.json` retains coordinates, formulas and workbook
hash; the original bytes were unchanged.
