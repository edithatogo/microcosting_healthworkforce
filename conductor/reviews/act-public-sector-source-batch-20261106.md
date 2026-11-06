# ACT public-sector source batch — 6 November 2026

Six source files linked from the [ACT Public Service agreement portal](https://www.cmtedd.act.gov.au/employment-framework/for-employees/agreements)
were retrieved and checked against their recorded SHA-256 hashes. The retained
original PDFs, text extractions and six validated candidate SourceRecords are in
the private workforce source inventory. The records are marked held and primary,
with applicability unresolved. The portal lists the health-sector instruments;
its current listing is discovery evidence rather than proof of a particular
worker's coverage or a complete variation history.

| Portal file | Source identity and bounded date evidence |
|---|---|
| [Administrative and Related Classifications](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0004/2287633/ACT-Public-Sector-Administrative-and-Related-Classifications-Enterprise-Agreement-2023-2026.pdf) | Decision 2023 FWCA 2928 records operation from 20 September 2023 and nominal expiry 31 March 2026. The portal says the 2026–2029 proposal was not approved by employees and describes continued coverage until a replacement takes effect. |
| [Support Services](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0011/2519948/ACTPS-Support-Services-EA-2023-2026.pdf) | The retrieved edition includes a variation decision and records original approval on 19 January 2024 and operation from 26 January 2024. |
| [Technical and Other Professionals](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0019/2382220/ACTPS-Technical-and-Other-Professionals-EA-2023-2026.pdf) | Decision 2024 FWCA 157 records operation from 23 January 2024; the edition also contains variation material. |
| [Medical Practitioners Determination](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0006/2979537/ACT-Public-Sector-Medical-Practitioners-Determination-2023-2026-Variation.pdf) | The actual file is a determination and a February 2026 variation, not merely an agreement matching the portal label. The decision states the determination commenced on 12 November 2025 and the correction operates from commencement. |
| [Nursing and Midwifery](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0007/2548897/ACTPS-Nursing-and-Midwifery-EA-2023-2026.pdf) | Decision 2024 FWCA 2886 records approval on 6 August 2024; clause 4.1 specifies operation seven days later, giving 13 August 2024. Worker scope and later variation history remain unresolved. |
| [ACT Ambulance Service](https://www.cmtedd.act.gov.au/__data/assets/pdf_file/0011/2410121/ACT-Public-Sector-Ambulance-Service-Enterprise-Agreement-2023-2026.pdf) | Decision 2024 FWCA 765 records operation from 6 March 2024. |

The nominal expiry in each retrieved document is 31 March 2026; this does not
establish that any instrument ceased on that date. The candidate registry does
not yet assert verified employer, position, classification, later variation,
pay-effective period, current instrument or redistribution rights. No values or
conditions are accepted for costing. The medical determination's different
legal form and retrospective correction must remain explicit when building a
versioned release.

## Coverage clauses and classification checks

The following are source-specific coverage criteria from the retrieved editions,
not a conclusion about present-day employment or an individual's coverage.
Physical PDF page numbers are given so the corresponding source can be checked.

| Edition | Coverage clause and evidence needed |
|---|---|
| Administrative | A3, PDF pages 21–22: specified ACT head of service, ACT statutory bodies and persons engaged under the Public Sector Management Act in Annex A classifications, subject to stated exclusions. The historical text also names Calvary. Verify the actual employer and relevant date; the historical wording does not establish a present employer relationship. |
| Support Services | A3, PDF pages 26–27: the specified ACT head of service and statutory bodies, and persons engaged under the Act in Annex A classifications, subject to stated exclusions. Obtain the role's actual classification and employing entity. |
| Technical and Other Professionals | A3, PDF pages 24–25: the specified ACT head of service and statutory bodies, with persons engaged under the Act or the named Calvary entity in Annex A classifications and stated exclusions. A generic job title or the historical entity name is insufficient to establish coverage. |
| Medical Practitioners Determination | Clause 3, PDF page 21: the specified ACT head of service, statutory bodies and persons engaged under the Act in Annex A classifications, with stated senior-role exclusions. Check the position and the determination's date, including the 2026 correction. |
| Nursing and Midwifery | Clause 3, PDF page 15: the specified ACT head of service and statutory bodies, and persons engaged under the Act in Schedule 1 classifications, with stated senior-role exclusions. The document's decision approves the agreement on 6 August 2024; clause 4.1 states operation seven days after approval. |
| Ambulance Service | A3, PDF pages 20–21: the specified ACT head of service, statutory bodies and persons engaged under the Act or the named Calvary entity in Annex A classifications, with stated exclusions. Determine the actual employing entity, position and period before selection. |

The [ACT health-professional edition](./act-health-professionals-source-20261106.md)
has a separate A3 and Annex A. Do not select one instrument solely because a
role sounds clinical, or treat all ACT public-sector employees as interchangeable.
The six candidate records remain unaccepted until later variations, employer and
position evidence, pay periods and rights are reviewed. The 2023–2026 nominal
expiry is not used as an automatic end date.

## Screening-register linkage

The seven held ACT candidates (the six files above and the health-professional
edition) are now linked as leads to ten ACT public-sector profession-family
targets in the private successor
`gap-screening-linked-act-batch-v2.csv`. The previous 576-target register is
preserved. An independent row comparison confirmed all 576 target identities
are unchanged and only the ten intended ACT/public rows changed their holding
status and next action. Each linked row remains `applicability_unassessed`;
several broad families are leads for further role-specific review, not claims
that every role in the family is covered. Multiple target links to one source
are not additional acquisitions. The successor file SHA-256 is
`e71771392db3121d0490856c993219c06a936d3e8d71946a86b4c6d8594eecbb`.

## Nursing commencement reconciliation

The retained nursing edition's approval decision is dated 6 August 2024 and
clause 4.1 states commencement seven days after approval. The resulting original
operative date is 13 August 2024; this is distinct from a wage-effective date
or an individual's first full pay period. The source PDF SHA-256 was rechecked
as `4da4c4943db2f61e25468af33d0f991c4ac8d835d9fe889fec82f605e2817b79`.
The private candidate successor `act-public-sector-six-source-candidates-v2.json`
(SHA-256 `701b1ed3bfd0cab032ae2a5743f6a2f8a22d69be04ad10453cf38b591e9ad5a5`)
records the operative date while keeping `applicability` unresolved and the
verification horizon unset. It does not decide employment, later variations,
current coverage or pay-period applicability; the previous file is preserved.
