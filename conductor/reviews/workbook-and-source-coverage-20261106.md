# Workbook intake and source coverage — 6 November 2026

## Frozen scope and evidence

Read-only assessment at private source 5f1e9322e1472c6f84d54134accdfdbe7a5d00b4. Workbook SHA-256: `c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca`. Original bytes were unchanged. Python 3.15.2/openpyxl inspection performed no save, recalculation or model run.

The workbook has **20 worksheets, 27,929 nonempty cells, 9,299 formulas and 94 contiguous nonempty-row regions**. There are no formal Excel table objects or workbook-global defined names. One sheet-local name, `Medicare Enrolments!IDX`, refers to title cell `$A$3`, not a data table. No external-workbook/query/pivot/embedded-object package parts were found. All 9,299 formula caches are absent in this retained file; native recalculation is required before evaluating formula results. Prior owner replay evidence is reused, not repeated here.

A physical region is an inventory unit, not necessarily one semantic table: adjacent horizontal outputs and stacked repeated headers require further splits. All 94 regions are registered below. Every worksheet has an explicit disposition, including the empty sheet; this is complete intake documentation, **not a claim that all tables already feed the calculator**. Current library intake is partial.

## Every worksheet: content, current consumption and required incorporation

| Worksheet | Used range; regions; formula count | Content | Current consumption | Required disposition |
|---|---|---|---|---|
| Labour - Prices | A1:BN124; 20; 2271 | Primary source metadata, 25 state-role inputs, Year 0–4 rates, unweighted aggregates and dollar/percentage components | Partial: parameters() reads the 25 rows and selected inputs/cached outputs; source metadata, aggregate/component tables are not exposed | Preserve legacy inputs; version metadata, each year/tier, components and aggregates separately |
| Labour - Prices (WM) | A1:BN160; 26; 2311 | Parallel input/rate/component tables plus Medicare-weighted ALL(WM) aggregates and placeholders | Not consumed by the calculation API | Extract as a distinct weighting/method variant; never pool ALL with individual state rows |
| Medicare Enrolments | A1:J41; 2; 0 | December 2023 enrolment counts, card-size distribution, denominator/method notes, source link | Not consumed | Preserve statistical reference and caveats; not workforce or activity-volume weights by default |
| Weightings | A1:H10; 1; 17 | Eight jurisdiction counts, five-state denominator, alternate reordered five-state fractions | Not consumed | Version denominator, included states, observation date and target estimand; require explicit weight selection |
| Components $ and % | A1:N64; 1; 0 | Two vertically stacked tables: dollar components and fractional shares; 30 rows each including ALL | Not consumed | Split A1:N32 and A33:N64; typed currency/share units despite reused percentage-looking headers |
| Labour - Prices (DSA) | A1:DH124; 19; 3024 | Independent DSA input LL/MP/UL, base and ten sensitivity axes, component subtables | Not used as runtime inputs | Preserve its own baseline and axes; explicit reconciliation against primary inputs |
| Labour - Prices (DSA, Values) | A1:BP33; 1; 0 | Archived wide base/sensitivity LL/MP/UL annual and hourly outputs | Read for delivered diagnostics only; not a passing acceptance gate | Preserve every axis/tier; retain incompatibility and false diagnostics |
| Labour - Prices (DSA,Val,Long) | A1:I332; 1; 0 | Long annual/hourly sensitivity outputs | Not consumed | Typed long archive; retain source identity, axes, units and duplicates |
| Labour - Prices (DSA,Val,Lo (2) | A1:F331; 1; 0 | Long hourly sensitivity outputs | Not consumed | Preserve distinct sheet identity; compare with related long archive rather than silently deduplicate |
| Labour - Prices (DSA, Pub) | A1:BG301; 1; 1440 | Numeric and formatted publication sensitivity blocks, ALL and jurisdiction rows | Not consumed | Split numeric/display blocks; retain bounds and presentation labels without asserting a statistical CI |
| Labour - Pr (PSA,Val,Long,Tot) | A1:F331; 1; 0 | Archived total-cost LL/MP/UL by sensitivity variable, despite PSA in sheet name | Not consumed | Classify from columns/content; not iteration-level Monte Carlo draws |
| Labour - Pr (PSA,Val,Hr) | A1:F31; 1; 0 | Archived baseline hourly LL/MP/UL across roles/jurisdictions | Not consumed | Keep as baseline bounds, not a distribution or empirical uncertainty sample |
| Sum Cost | A1:E6; 1; 0 | Formatted five-role ALL cost/rate summaries | Not consumed | Presentation layer; keep numeric provenance and bound semantics explicit |
| Sum Cost Jur | A1:H73; 12; 50 | Jurisdiction numeric LL/mid/UL plus formatted summaries and label-only placeholders | Not consumed | Separate numeric tables, display text and intentional placeholders |
| Sum Cost Comp | A1:M21; 2; 0 | Mean component parameters/salary range strings plus notes/table fragments | Not consumed | Retain aggregate method and parameter provenance; do not reuse aggregates as individual inputs |
| Labour - BY ($) | A1:N31; 1; 0 | Base-year dollar components and salary tiers for 25 state-role plus five ALL rows | Not consumed | Version component units and distinguish aggregate from input rows |
| Labour - BY (%) | A1:A1; 0; 0 | Empty worksheet | Not consumed; explicitly empty | Register empty state; no inferred values or invented percentage table |
| Labour - Prices (Fixed header) | A1:X26; 1; 186 | 25-row flat alternative inputs/cost/rate table | Not consumed | Normalize only with declared units; indexation is 1.5 here versus 0.015 in primary table |
| Assumptions | A1:B6; 1; 0 | Five explicit modelling rationales | Not consumed as a machine-readable assumptions register | Carry assumption IDs into outputs; separate entitlements, uptake, average penalties and indexation |
| PSA - Validation | A1:A2; 1; 0 | Single expected-mean literal 150000 | Generic loader exists; current CLI PSA does not establish this as an authoritative reference | Preserve historical literal and introduction provenance; exclude as scientific acceptance oracle |

## Consequences for costing

- The active model covers five roles (lab technician, medical scientist, administration, bioinformatics and pathologists) in VIC, SA, NSW, QLD and WA: 25 input combinations. ACT, NT and TAS appear in the enrolment reference, but have no workforce costing rows. Nurses/midwives, most allied-health/dental/pharmacy/paramedic/Aboriginal-health roles and wider support classifications are not represented as priced workforce inputs. Presence of a candidate document is not model coverage.
- The original model contains unweighted ALL aggregates and a separate WM variant. The WM midpoints are enrolment-weighted; lower/upper values remain MIN/MAX-derived bounds, not weighted quantiles or confidence intervals. Some bound formulas refer through other aggregates/formatted rows, so formula lineage must be preserved and reviewed. Its weights are Medicare enrolment weights, not observed workforce FTE, service volumes or patient-level resource use. The current PSA unweighted 25-row mean is a different estimand; no automatic replacement is justified.
- The workbook projects Year 0–4. The current default projection function produces Year 0–5. Existing base-year parity does not prove every future-year worksheet output is incorporated or reconciled.
- The fixed-header indexation value 1.5 and primary value 0.015 require explicit percent/fraction metadata. Repeated percentage-like headers also label currency contributions in component tables. Unit inference from a header alone is unsafe.
- Assumptions explicitly describe public-holiday penalties as averages; sick-leave 4.6% as non-empirical institutional judgement; generalised 1.5% indexation; 100% annual-leave use and professional-development allowance uptake. These are model choices, not interchangeable legal entitlements.
- Legacy annual-cost/leave-cover numerator and productive-time denominator semantics remain immutable in compatibility mode. Version 2 must explicitly distinguish paid cost, incremental leave cover, productive capacity and activity allocation to prevent double counting.
- DSA archived baselines and axes differ from current configured perturbations. The GHA handoff documents all 17 false archived diagnostics and why they are not acceptance oracles. Sheets with PSA in their names contain bounds/sensitivity summaries, not evidence of a Monte Carlo distribution.
- Publication labels such as 95% CI must be preserved verbatim as archive text without making a new statistical validity claim. The unexplained 150000 reference remains archival.

## Source holdings and limits

The current tracked data directory holds the workbook and three JSON configurations. No award/contract PDF or DOCX is present in the current checkout or its frozen primary checkout. A full-history filename inspection found no tracked source PDF/DOCX. Historical `b486e6d:data/source_docs/DOCUMENT_MAP.md` and `data/source_validation/VIC_Health_EA_2017_2021.json` remain available in merged history, but no corresponding primary document is held. The latter is an unverified derived transcription, not an authoritative award.

The historic map mixes awards, agreements, wage schedules, position descriptions, policy documents, an email, a costing workbook and unidentified filenames. It also puts national instruments under state headings and reverses Nurses/Medical Practitioners award codes. These entries are discovery leads only. No private email, intranet document or employer contract is presumed redistributable.

## Workbook profession/instrument gap matrix

Every existing row has a source-to-parameter verification gap because the actual instrument edition and cited clause/page are not held. More specific problems follow.

| Jurisdiction | Existing five-role references | Priority gaps |
|---|---|---|
| VIC | Lab technician: D4 (HPA); Medical scientist: D5 (MSEBA); Admin staff: D6 (HPA); Bioinformatics staff: D7 (MCRI Professional and Administrative Salaries); Pathologists: D8 (MEDICAL SPECIALISTS (VICTORIAN PUBLIC HEALTH SECTOR) (AMA VICTORIA/ASMOF) (SINGLE INTEREST EMPLOYERS) ENTERPRISE AGREEMENT 2022 – 2026) | Resolve HPA/MSEBA abbreviations; grade/reference mismatch (admin 3–5 cites HS5–HS7); MCRI employer-specific bioinformatics applicability; retrieve historical and current scientists/specialists editions. |
| SA | Lab technician: D10 (S.A. PUBLIC SECTOR SALARIED EMPLOYEES INTERIM AWARD); Medical scientist: D11 (MEDICAL SCIENTISTS (SOUTH AUSTRALIAN PUBLIC SECTOR) AWARD); Admin staff: D12 (S.A. PUBLIC SECTOR SALARIED EMPLOYEES INTERIM AWARD); Bioinformatics staff: D13 (S.A. PUBLIC SECTOR SALARIED EMPLOYEES INTERIM AWARD); Pathologists: D14 (SA Health Salaried Medical Officers Enterprise Agreement 2022) | Recover authoritative salary schedules and agreement/award combination for technical, ASO/PO, scientists and medical officers; distinguish private costing-table/email evidence from pay authority. |
| NSW | Lab technician: D16 (Health Employees (State) Award); Medical scientist: D17 (Hospital Scientists (State) Award); Admin staff: D18 (MISSING); Bioinformatics staff: D19 (Hospital Scientists (State) Award); Pathologists: D20 (STAFF SPECIALISTS (STATE) AWARD 2022) | Administration award cell D18 is blank; resolve applicable awards/classifications for technician, scientists/bioinformatics and staff specialists plus current variations/determinations. |
| QLD | Lab technician: D22 (Hospital and Health Service General Employees (Queensland Health) Award - State 2015); Medical scientist: D23 (Hospital and Health Service General Employees (Queensland Health) Award - State 2015); Admin staff: D24 (Hospital and Health Service General Employees (Queensland Health) Award - State 2015); Bioinformatics staff: D25 (Hospital and Health Service General Employees (Queensland Health) Award - State 2015); Pathologists: D26 (MEDICAL OFFICERS (QUEENSLAND HEALTH) AWARD – STATE 2015) | HP2–3 scientist row cites a general-employees award; verify the governing HP/dental versus general-stream instruments and agreements without inferring coverage from the abbreviation. Resolve grades for technician/admin/bioinformatics and medical L18–L27. |
| WA | Lab technician: D28 (Health Salaried Officers Agreement); Medical scientist: D29 (Health Salaried Officers Agreement); Admin staff: D30 (Health Salaried Officers Agreement); Bioinformatics staff: D31 (Health Salaried Officers Agreement); Pathologists: D32 (WA HEALTH SYSTEM – MEDICAL PRACTITIONERS – AMA INDUSTRIAL AGREEMENT 2022) | Health Salaried Officers Agreement is insufficiently identified (no edition/parties in row metadata); verify G/P grade mappings, PACTS/HSU sources, medical agreement and supplementary conditions. |
| ACT | No workforce input rows; enrolment denominator only | Acquire all priority profession/sector instruments and classification/rate/condition mappings; no inherited priced baseline. |
| NT | No workforce input rows; enrolment denominator only | Acquire all priority profession/sector instruments and classification/rate/condition mappings; no inherited priced baseline. |
| TAS | No workforce input rows; enrolment denominator only | Acquire all priority profession/sector instruments and classification/rate/condition mappings; no inherited priced baseline. |

All eight jurisdictions also lack complete current nursing/midwifery, allied health, pharmacy/dental, ambulance/paramedic, Aboriginal and Torres Strait Islander health, health-science, technical/assistant, administrative/managerial, operational/support, research/academic and contractor/agency coverage. These are acquisition/verification gaps, not findings that an occupation is award-free. Sector and employment type must be part of applicability.

## Verified primary discovery entry points

Checked 6 November 2026. These are public source entry points, not downloaded, extracted or accepted parameter releases. Retrieve instrument text, variations, wage schedules and approval/operative dates before admitting any value.

| Jurisdiction/system | Authoritative discovery route |
|---|---|
| NSW | [NSW Health awards and determinations](https://www.health.nsw.gov.au/careers/conditions/Pages/awards.aspx) |
| QLD | [Awards, agreements and orders](https://www.careers.health.qld.gov.au/working-for-us/awards-agreements-and-orders); [wage rates by stream](https://www.health.qld.gov.au/hrpolicies/wage-rates) |
| VIC | [Department of Health enterprise agreements](https://www.health.vic.gov.au/health-workforce/enterprise-agreements) |
| SA | [Attorney-General current agreements](https://www.agd.sa.gov.au/industrial-relations/current-agreements); [SAET agreement register](https://www.saet.sa.gov.au/awards-agreements-and-registers/enterprise-agreements/) |
| WA | [WA Health system industrial library](https://www.scgh.health.wa.gov.au/sitecore/content/Corporate/Articles/A_E/Awards-and-Agreements); [archive](https://www.health.wa.gov.au/Articles/A_E/Awards-and-Agreements/Awards-and-Agreements-archive) |
| TAS | [TIC public-sector agreements](https://www.tic.tas.gov.au/public_sector_agreements); [public-sector awards](https://www.tic.tas.gov.au/all_public) |
| ACT | [ACT health enterprise agreements](https://www.act.gov.au/work-with-act-government/act-government-health-careers/enterprise-agreements); [ACTPS register](https://www.cmtedd.act.gov.au/employment-framework/for-employees/agreements) |
| NT | [OCPE current enterprise agreements](https://ocpe.nt.gov.au/employment-terms-and-conditions/current-enterprise-agreements/enterprise-agreements-current) |
| National / private / not-for-profit | [FWO award list](https://www.fairwork.gov.au/employment-conditions/awards/list-of-awards): [Medical Practitioners MA000031](https://awards.fairwork.gov.au/MA000031.html), [Nurses MA000034](https://awards.fairwork.gov.au/MA000034.html), [Health Professionals and Support Services MA000027](https://awards.fairwork.gov.au/MA000027.html). Applicability and other instrument families require employer/occupation verification. |

Nominal expiry, approval date, conditions commencement, pay-effective date, first-full-pay-period rules and backpay/payment date must be distinct. An expired nominal term is not evidence that an agreement has ceased to apply. No universal precedence or award selection is inferred from state/profession alone.

## Complete physical-region ledger

Every nonempty cell belongs to one listed contiguous-row region. Empty/label-only regions are retained. Semantic subdivisions and typed incorporation are an implementation acceptance criterion, not silently claimed complete.

### WS01 — Labour - Prices

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS01-R01 | A1:BN8 | 414 |
| WS01-R02 | A10:BN14 | 319 |
| WS01-R03 | A16:BN20 | 316 |
| WS01-R04 | A22:BN26 | 313 |
| WS01-R05 | A28:BN32 | 315 |
| WS01-R06 | A34:BN38 | 295 |
| WS01-R07 | A40:BL44 | 145 |
| WS01-R08 | A46:X51 | 71 |
| WS01-R09 | A53:X57 | 70 |
| WS01-R10 | A59:X63 | 70 |
| WS01-R11 | A65:X69 | 70 |
| WS01-R12 | A71:X75 | 70 |
| WS01-R13 | A77:X81 | 70 |
| WS01-R14 | A83:X87 | 70 |
| WS01-R15 | A89:X94 | 71 |
| WS01-R16 | A96:X100 | 70 |
| WS01-R17 | A102:X106 | 70 |
| WS01-R18 | A108:X112 | 70 |
| WS01-R19 | A114:X118 | 70 |
| WS01-R20 | A120:X124 | 70 |

### WS02 — Labour - Prices (WM)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS02-R01 | A1:BN8 | 414 |
| WS02-R02 | A10:BN14 | 319 |
| WS02-R03 | A16:BN20 | 316 |
| WS02-R04 | A22:BN26 | 313 |
| WS02-R05 | A28:BN32 | 315 |
| WS02-R06 | A34:BN38 | 295 |
| WS02-R07 | A40:BL44 | 145 |
| WS02-R08 | A46:AD50 | 40 |
| WS02-R09 | A52:AB56 | 20 |
| WS02-R10 | A58:X63 | 71 |
| WS02-R11 | A65:X69 | 70 |
| WS02-R12 | A71:X75 | 70 |
| WS02-R13 | A77:X81 | 70 |
| WS02-R14 | A83:X87 | 70 |
| WS02-R15 | A89:X93 | 70 |
| WS02-R16 | A95:X99 | 70 |
| WS02-R17 | A101:B105 | 10 |
| WS02-R18 | A107:B111 | 10 |
| WS02-R19 | A113:X118 | 71 |
| WS02-R20 | A120:X124 | 70 |
| WS02-R21 | A126:X130 | 70 |
| WS02-R22 | A132:X136 | 70 |
| WS02-R23 | A138:X142 | 70 |
| WS02-R24 | A144:X148 | 70 |
| WS02-R25 | A150:B154 | 10 |
| WS02-R26 | A156:B160 | 10 |

### WS03 — Medicare Enrolments

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS03-R01 | A1:A3 | 3 |
| WS03-R02 | A5:J41 | 208 |

### WS04 — Weightings

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS04-R01 | A1:H10 | 52 |

### WS05 — Components $ and %

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS05-R01 | A1:N64 | 870 |

### WS06 — Labour - Prices (DSA)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS06-R01 | A1:DH8 | 705 |
| WS06-R02 | A10:DH14 | 539 |
| WS06-R03 | A16:DH20 | 536 |
| WS06-R04 | A22:DH26 | 533 |
| WS06-R05 | A28:DH32 | 535 |
| WS06-R06 | A34:DH44 | 700 |
| WS06-R07 | A46:AT51 | 71 |
| WS06-R08 | A53:AT57 | 70 |
| WS06-R09 | A59:AT63 | 70 |
| WS06-R10 | A65:AT69 | 70 |
| WS06-R11 | A71:AT75 | 70 |
| WS06-R12 | A77:AT81 | 70 |
| WS06-R13 | A83:AT87 | 70 |
| WS06-R14 | A89:AT94 | 71 |
| WS06-R15 | A96:AT100 | 70 |
| WS06-R16 | A102:AT106 | 70 |
| WS06-R17 | A108:AT112 | 70 |
| WS06-R18 | A114:AT118 | 70 |
| WS06-R19 | A120:AT124 | 70 |

### WS07 — Labour - Prices (DSA, Values)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS07-R01 | A1:BP33 | 2141 |

### WS08 — Labour - Prices (DSA,Val,Long)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS08-R01 | A1:I332 | 2981 |

### WS09 — Labour - Prices (DSA,Val,Lo (2)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS09-R01 | A1:F331 | 1986 |

### WS10 — Labour - Prices (DSA, Pub)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS10-R01 | A1:BG301 | 5291 |

### WS11 — Labour - Pr (PSA,Val,Long,Tot)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS11-R01 | A1:F331 | 1986 |

### WS12 — Labour - Pr (PSA,Val,Hr)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS12-R01 | A1:F31 | 186 |

### WS13 — Sum Cost

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS13-R01 | A1:D6 | 24 |

### WS14 — Sum Cost Jur

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS14-R01 | A1:H7 | 50 |
| WS14-R02 | A9:H13 | 40 |
| WS14-R03 | A15:H19 | 40 |
| WS14-R04 | A21:H25 | 40 |
| WS14-R05 | A27:H31 | 40 |
| WS14-R06 | A33:H37 | 40 |
| WS14-R07 | A39:F43 | 20 |
| WS14-R08 | A45:F49 | 20 |
| WS14-R09 | A51:F55 | 20 |
| WS14-R10 | A57:F61 | 20 |
| WS14-R11 | A63:F67 | 20 |
| WS14-R12 | B69:B73 | 5 |

### WS15 — Sum Cost Comp

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS15-R01 | A2:M7 | 78 |
| WS15-R02 | A9:F21 | 78 |

### WS16 — Labour - BY ($)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS16-R01 | A1:N31 | 434 |

### WS17 — Labour - BY (%)

Empty; registered explicitly.

### WS18 — Labour - Prices (Fixed header)

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS18-R01 | A1:X26 | 624 |

### WS19 — Assumptions

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS19-R01 | A1:B6 | 12 |

### WS20 — PSA - Validation

| Region ID | Range | Nonempty cells |
|---|---|---|
| WS20-R01 | A1:A2 | 2 |


## Machine-readable candidate and gap registers

- [Historical source candidates](./source-candidate-register-20261106.json) retain every enumerated filename/pattern and original map line, with holding/classification/identity issues. Patterns and filename ranges are not expanded into invented holdings.
- [Initial source-gap screening matrix](./workforce-source-gap-screening-20261106.csv) covers eight jurisdictions × 12 broad families × six sectors (576 screening cells). All require applicability/source work. This is an initial planning denominator, not 576 distinct instruments or an exhaustive employer/occupation census. Legacy row references indicate only workbook mentions, not verified sector coverage.

The historical derived VIC parameter transcription is recoverable at
`b486e6d:data/source_validation/VIC_Health_EA_2017_2021.json`; its original primary
PDF is not held and its values are not admitted as source-verified conditions.
