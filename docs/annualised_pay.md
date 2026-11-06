# Complete-window annualised-pay comparison

`src.annualised_pay.compare_annualised_pay(rule, request, earnings)` compares
explicitly supplied annualised wages with the complete alternative agreement
wages for one selected window. It sums each side first, then computes one exact
shortfall: `max(0, agreement_total - annualised_total)`. Signed period differences
remain visible. For example, a 200 gain and a 200 loss cancel over the window;
applying a floor separately to each fortnight would invent a 200 top-up.

The caller supplies a reviewed `AnnualisedPayRule` with exact source/hash/citation,
jurisdiction/employer/classification, operative dates, knowledge date, currency,
comparison-period count and complete component names for each side. The method
supports consecutive fortnightly periods. It checks each supplied interval as
two local calendar weeks in the selected timezone; daylight-saving transitions
can change elapsed UTC hours. No fixed 336-hour comparison duration is inferred.

An `AnnualisedPayRequest` identifies one opaque case and an explicitly complete
`PeriodCalendar`, eligibility basis and complete-wage assertion. The calendar
must have exactly the selected count. Each `WagePeriodEvidence` covers exactly
one calendar period with a unique period ID. It retains all declared components,
explicit known zeros, currency, economic dates, paid/counterfactual/scenario
labels, evidence IDs/hashes and knowledge dates. Missing/extra components, null
or negative amounts, duplicate/missing intervals and uncovered source scope fail.
Reviewed source assertions do not independently establish a real employee's
eligibility or the correctness of the upstream counterfactual wages.

The wage amounts can be exact Decimal or Fraction values. The returned
`AnnualisedPayComparison` retains every input row, exact per-period and whole-
window totals, one shortfall, the annualised total plus that shortfall, rule hash,
source and case lineage. The result is a scenario when any supplied wage or
settlement-convention input is an analyst assumption. Observed-pay labels require
completed economic periods and known evidence; a label is not an independent
payroll audit. Upstream calculations must include the applicable wage/penalty/
allowance/leave rules and their source editions; this function does not derive
those amounts from an annual salary or average roster.

## Review and payment timing

Set `review_requested` explicitly. Pending or unrequested review leaves payment
timing null while retaining the comparison amount. A completed review supplies
`ReviewSettlement`: an aware completion instant, a complete payment calendar,
and an explicit reviewed or assumed boundary convention with its basis.
The supported convention selects the first **complete period starting strictly
after** review completion. At an exact boundary this excludes the period starting
at that instant. This interpretation is declared, not silently inferred from a
legal phrase. A different interpretation needs a separately qualified method.

The review must follow the complete comparison window and be known at the selected
knowledge date. The payment calendar must include a boundary at/before completion
and cover the whole next period. A positive shortfall returns that period; no
shortfall returns no settlement period. The output identifies a period, not a
payment day or evidence of cash paid. It does not change a payroll ledger, send
instructions or repeat an amount already included in actual wages.

## Source qualification

One source may require six fortnightly periods, a specific employer/grade,
annualised-pay arrangement, an employee request and a review before settlement.
The release author must qualify those facts and select that rule. No count,
employer, classification, salary rate, written arrangement or entitlement is
selected automatically. This API supports source-specific qualification; the
synthetic tests do not accept a national rule or resolve conflicting source text.
