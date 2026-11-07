# Explicit component dependencies

`cost_derived_snapshot` and `cost_derived_activity` add reviewed, ordered
fractional rules to the existing condition-cost ledger. Each rule identifies
its own source, effective dates, fraction and named earlier component bases.
Names must be unique, and a missing or later dependency is rejected. The result
retains the base ledger and exact fractional amounts for each added rule and date.

For example, if an allowance is a reviewed fraction of salary and a separate
reviewed rule includes that allowance in an on-cost base, define the allowance
first and the incremental on-cost second. Do not add the full salary on-cost a
second time if it is already in the base ledger. The ACT health-professional
agreement's advanced-skill allowance illustrates a possible interaction, but
its eligibility, approval, applicable on-cost rate and source period must be
verified for the worker; the library does not infer them.

This method is additive. It does not infer entitlements, rule precedence,
thresholds, caps, payroll rounding or a rule for an uncovered date. Dynamic
costing validates each local-day segment; it does not automatically switch to
another rule edition when a rule stops applying.

## Retrospective derived rules

A derived rule may separately carry reviewed retrospective authority. Its
knowledge date must match the condition release, and its source hash and scope
are verified at the authority and knowledge dates. An earlier work date must
fall inside the rule's own reviewed entitlement interval. The salary's
retrospective authority does not automatically approve an allowance or on-cost.
This is a costing scenario and does not determine worker eligibility, legal
effect, backpay or cash timing.

## NT Aboriginal Health Practitioner shift allowance

For a verified 38-hour shift role under clauses 37.5–37.6, use a derived
component with fraction `0.034` and the salary component as its sole base.
For a part-time appointment, apply the fraction to salary for the paid
hours being costed. Applying a second FTE factor would reduce the allowance
twice. Keep appointment eligibility and the effective salary edition with
the case evidence.

[NTPS Aboriginal Health Practitioner agreement, clauses 37.5–37.6](https://ocpe.nt.gov.au/__data/assets/pdf_file/0007/1588894/ntps-aboriginal-health-practitioner-2025-2029-enterprise-agreement.pdf)

### NT Aboriginal health practitioner exemplary practice allowance

Schedule D of the [2025–2029 enterprise agreement approval bundle](https://ocpe.nt.gov.au/__data/assets/pdf_file/0008/1604663/northern-territory-public-sector-aboriginal-health-practitioner-2025-2029-enterprise-agreement.PDF)
defines Exemplary Practice 1 as 6% of the fourth salary point of AHP2
or AHP3, as applicable. Exemplary Practice 2 uses 13% of the fourth
salary point of AHP3. The schedule publishes annual amounts. Use the
applicable dated annual amount with the unit-quote calculator once
the employee's eligibility, payment quantity and effective release
have been reviewed. A salary-relative derived component would use the
employee's own salary and can produce the wrong result for this allowance.

Clauses 46.3–46.9 restrict eligibility to approved, non-casual AHP2
and AHP3 employees and require reassessment after three years. Under
46.12–46.13, payment is fortnightly and prorated by agreed hours for
part-time employees. Include approved paid leave, exclude unpaid or
unauthorised leave, and exclude higher duties except under 44.9.
Include the allowance in the superannuation base and exclude it from
overtime and penalty bases. AHP3 EP1 and EP2 are mutually exclusive.
Use a reviewed payroll quantity for a dated payment, since Schedule D
expresses the rate annually. Clause 44.10 separately affects higher-duties
rate selection when current salary inclusive of the allowance meets or
exceeds the higher position's minimum. Review Annexure A before accepting
a release.

For AHP3, apply the [exclusive quote group](exclusive_quotes.md) to EP1
and EP2 allocations in the same costing request. Use the employee as
the resource and the reviewed entitlement interval as the exposure
window. Split windows where the accepted quote or approved status
changes. Validate the set together so overlapping allocations can be
detected. Keep the selected allowance as a separate component when
applying the reviewed superannuation base.
