# ACT health professionals source qualification — 6 November 2026

The ACT government's [Health Professional Enterprise Agreement 2023–2026 edition](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0006/2510448/ACTPS-Health-Professional-Enterprise-Agreement-2023-2026.pdf)
was retrieved as a 242-page PDF and its SHA-256 verified as
`f40633d0c73c4c9e134ff8e274c8740a91e82e5976a2eafa01111f02f7b25137`.
A validated candidate SourceRecord and the original bytes are retained privately;
the record is held and primary, with applicability unresolved.

The included Fair Work Commission decisions record original approval on 13 June
2024 and operation from 20 June 2024. A 20 January 2026 decision corrects
medical-imaging level 3–3.5 pay rates and states that its variation operates
from 20 June 2024 (PDF pages 1–2). The document also records earlier variations
in 2024 and 2025. This is a concrete example where agreement commencement,
published rate dates, variation decision and retrospective operation must remain
separate; a later knowledge date must not silently alter an earlier frozen run.
The agreement's nominal expiry is 31 March 2026. That date alone does not establish
cessation; later variations, replacement and applicability after this edition
remain to be checked.

Clause A3 (PDF page 26) ties coverage to the specified ACT employer and persons
in Annex A classifications, subject to stated exclusions. Clauses B15 and B17
(PDF pages 36 and 38) distinguish rostered shift and non-shift positions and
allow position-specific 36.75- or 38-hour ordinary weeks. The non-shift clause
states that standard hours are for salary and leave calculations. Section N
(PDF page 150 onward) describes an advanced-skill allowance with eligibility,
application and approval requirements; it is not an automatic loading for every
health professional.

The workbook contains no ACT-priced row. These findings therefore establish
an evidence-bearing candidate and a genuine source route, not a completed ACT
condition release or the classification, roster, allowance eligibility or rate
of an individual. Verify the exact employer and position, Annex A version,
relevant date, later instruments and source rights before accepting any rule.

## Structured candidate extraction

A private, source-hash-verified candidate batch records four alternative
position-specific weekly-hours facts (shift/non-shift and 36.75/38 hours), the
5% advanced-skill allowance and four first-full-pay-period timing clauses from
the separate administrative, support, technical and ambulance editions. The
allowance candidate retains its application/approval, exclusion, once-only,
part-time and superannuation qualifications. The timing candidates retain the
1 June 2023 trigger separately from any actual payroll commencement.

The nine records identify clause, PDF page and source edition and deliberately
leave individual applicability, accepted effective date, knowledge date and
rights unresolved. They are retained at
`.private-runs/workforce-source-coverage-20261106/act-condition-candidates-v1.json`
with SHA-256
`dc305e8e5e4573ca9c648a215b9dd57a75a3eb24ed5e5864ae31e8a2251830a8`.
They are candidate interpretations, not an accepted release or proof of a
specific worker's entitlement. Actual payroll calendars and approval histories
were not supplied.

## Allowance lifecycle and professional-lead tiers

The source's N2.8–N2.9 (PDF page 151) distinguishes cessation on promotion,
a possible cessation during higher duties, specified transfers and eligibility
loss subject to panel endorsement, plus five-year reapplication. These are
separate candidate events; a model must not turn the discretionary higher-duties
case into automatic cessation or assume reapplication itself proves termination.

N3.1 and N3.5–N3.6 (PDF pages 151–152) describe a separate professional-lead
allowance with selection and classification conditions and tier percentages of
a separately calculated allowance: 10% for groups of 10 or fewer, 40% for
11–50, and 100% for 51 or more. These are not fractions of salary and must not
be fed directly into a salary-percentage rule. The underlying allowance,
role, group count, employment scope and source edition require qualification.

A private successor `act-condition-candidates-v2.json` adds eight structured
candidates for these clauses and retains all nine v1 records byte-for-value.
All 17 remain applicability-unresolved and unaccepted. The successor SHA-256 is
`f27eff4e0e3a65bd552189273e453f104a4c523a8d4c392e911f0dc011baa61b`;
source bytes and earlier artifacts remain unchanged.

## Professional-lead table and arithmetic

Annex C (physical PDF page 220) expresses the professional-lead allowance as
annual amounts paid in fortnightly instalments. Its note describes the
calculated allowance as the difference between the HP4.2 and HP5.2 paypoints at
agreement commencement. It states that the allowance is not paid during unpaid
leave and is paid for all purposes. Eligibility and the selection process remain
as in section N; these observations do not establish an individual entitlement.

The private v3 candidate batch preserves the earlier 17 records and adds 15
table amounts across the five populated date columns and three tiers. Header
dates are recorded as displayed, not automatically treated as individual
pay-effective dates. For the five columns, comparing the published level-2 and
level-1 whole-dollar amounts with 40% and 10% of the published level-3 amount
produces differences of up to $0.60 and $0.40 per annum respectively. These
small discrepancies demonstrate why the published values and calculation
lineage must both be preserved; they do not establish the source's rounding
method or justify silently adjusting an amount.

The successor is `.private-runs/workforce-source-coverage-20261106/act-condition-candidates-v3.json`
(SHA-256 `3d7b1499f79c7b655b144a5365f51b0593d4077a0d4ed2096b7137d361b80f32`);
the private arithmetic receipt is `act-professional-lead-arithmetic-v1.json`
(SHA-256 `c2a7c73687b74b626ab3c8917052e9a16d5f40a13675819ace567f4ff9512e15`).
All 32 candidate records remain unaccepted, with applicability and rights
unresolved. Prior versions and source bytes are retained.

## Professional-lead calculation-basis discrepancy

Annex C says the calculated professional-lead allowance is the difference
between HP4.2 and HP5.2 pay points at agreement commencement. The retrieved
Annex A (physical PDF page 180) has both old and newly translated classification
columns, including a column expressly conditional on the agreement operating
before 6 June 2024. The included decision records actual operation on 20 June
2024; therefore that conditional column must not be automatically selected as
the operative commencement rate.

A bounded comparison of the printed figures found that the obvious new HP5.2
minus new HP4.2 in the 6 June 2024 column is $23,612, while the Annex C
level-3 table in that date column is $19,791. Other inspected old and translated
column pairings also do not directly reproduce the corresponding displayed
amounts. These are comparisons of printed figures, not an assertion that the
source is wrong: the intended commencement basis, actual first full pay period,
classification transition, earlier calculation and any relevant variation have
not been established. Keep the published allowance and the calculation-basis
note as separate candidates; do not calculate one from the other or accept a
rate until reconciled.

The private receipt `act-lead-basis-comparison-v1.json` records the four tested
pairings and source hash (receipt SHA-256
`8c413a549e7d73f261d618ce804019a46e9ea17941004f9cae08e5584e2228f6`).
No actual payroll calendar, worker classification or individual eligibility was
inferred.

The Annex A and Annex C pages were subsequently rendered and visually checked:
the inspected HP4.2 and HP5.2 values align with the relevant classification
columns, and the $19,791 figure aligns with the level-3 allowance row and 6 June
2024 header. The alignment check does not resolve the calculation-basis or
pay-period questions above. The private page captures are
`act-health-professionals-annex-a-page180.png` (SHA-256
`1b583e81d537548250ddea80deb91df73277506ea5594acba933631e27d66d3c`) and
`act-health-professionals-annex-c-page220.png` (SHA-256
`e961d8f679a67175302b88a4ae88f9f040dff19b6cbe5cbe03e8145889fe9847`).

## Indexed historical-gap hypothesis

The official [2021–2022 agreement](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0006/1900734/ACT-Public-Sector-Health-Professional-Enterprise-Agreement-2021-2022-FINAL.pdf)
lists 9 June 2022 HP4.2 and HP5.2 annual rates of $123,710 and $142,352,
respectively, a $18,642 difference. The classification and amounts were visually
checked on physical PDF page 178, with the date header on the preceding page.
The later agreement's Annex C lists a sequence of percentage increases in its
allowance-table headers. Applying those seven listed percentage factors
sequentially to the historical $18,642 gap, without intermediate rounding,
reproduces all five published level-3 amounts from December 2023 through
December 2025 when rounded to whole dollars. The largest unrounded difference
from the published whole-dollar figures is less than $0.42 per year.

This is a strong arithmetic lead for the table's calculation lineage, not proof
that the parties intended this method, of the applicable payroll rounding rule,
or that any individual qualifies. The stated commencement basis, classification
translation and actual pay-period effect still require source or payroll
confirmation. Preserve the published table amounts and the hypothesis separately;
do not replace one with the other or accept an entitlement on this comparison.

The previous agreement is retained privately with SHA-256
`839125e3df9a66b1e2b69f535f74ce83476771476515bebdf8fe2b4fca365696`.
Its validated held-primary candidate record remains applicability-unresolved in
`act-health-professionals-2021-2022-candidate.json` (SHA-256
`b248315a2ffd4529cf97b129a224f40ef86e5154ae52162af0becb0e0df7642b`); its
approval decision states operation from 11 February 2022 and nominal expiry on
31 October 2022. Nominal expiry is not treated as an operative end date.
The reproducible arithmetic receipt `act-lead-indexed-2022-gap-v1.json` has
SHA-256 `938fc999969fb442d72f05e6b5b45bd607e7593a68805fec5cc4b5f935f20cbd`;
the 2023–2026 source hash is recorded above.
