# SA scientist overtime capability review — 6 November 2026

The retained [Medical Scientists award](https://www.saet.sa.gov.au/app/uploads/2023/07/279p-Award-July-2023.pdf),
PDF page 13, distinguishes MS1/MS2 ordinary hours from the nominal hours of
MS3 and above. Its historical clause 6.2 sets out authorised MS1/MS2 overtime,
a maximum-MS1 salary basis for MS2 overtime, a three-hour daily tier, special
weekend and public-holiday rates, daily calculation, quarter-hour computation,
a minimum time worked and agreed time off in lieu. The next page contains recall
provisions. The scanned page was visually checked. Applicability, any enterprise
agreement changes and an individual employee's classification remain unverified.

The current cumulative salary-overtime method assumes an uncapped salary basis
and nonnegative premium added to ordinary base pay. It cannot represent the
full cited interaction, and a generic 1.5 multiplier must not be presented as
implementing this award. A synthetic weekday example illustrates the accounting:
if four authorised overtime hours have an ordinary salary rate of $50/hour but
the explicitly applicable MS1 cap is $40/hour, and no weekend, holiday, recall
or time-off rule applies, the cited tier structure gives three hours at 1.5 and
one at 2.0, or $260. If an existing base ledger has already charged $200 for
those hours, the adjustment is $60. Depending on the cap and tier, an adjustment
to already-counted base can also be negative; an always-positive premium is not
a general solution. These are synthetic assumptions, not an accepted award
calculation for an individual.

Implementation needs an explicitly sourced cap and effective period, local-day
and roster history, an authoritative holiday calendar, eligibility, selection of
cash versus time off, a declared rounding convention including tie handling,
recall grouping, and a non-double-counting interaction with existing base pay.
Tests must independently cover the three-hour boundary, capped and uncapped
salary, negative adjustments, midnight and weekend transitions, public-holiday
precedence, quarter-hour and minimum-duration boundaries, recall overlaps and
time-off choices. The clause alone does not settle every interaction; reject
unreviewed combinations rather than infer precedence. The private source and
synthetic arithmetic receipt retains the source hash and clause references.

## Implementation follow-up

The daily capped overtime engine now covers an explicit salary cap and
signed adjustment to the base ledger. Its synthetic tests check tier
boundaries, prior history, unchanged allowances and rejection of bundled
salary. The cumulative-tier and session engines cover separate threshold
methods. All 20 focused tests across these three engines passed at 224f1d6.
The complete SA rule still requires current instrument and worker scope,
and reviewed interaction evidence for rounding, holiday precedence, recall
and time off in lieu.

## 2026 agreement interaction

The [SA Public Sector Enterprise Agreement (Salaried) 2026](https://www.saet.sa.gov.au/app/uploads/2026/03/SA-Public-Sector-Enterprise-Agreement-Salaried-2026-04032026.pdf)
links clause 15 to clause 6.1.3 of the Salaried Employees Interim Award.
That table lists the Medical Physicist ceiling at the top MPH-2 increment.
The Medical Physicist appendix separately applies the Medical Scientists
Award safety net and maps clause 6.2 references to MPH-1 registrars, with
a cross-reference to clause 15. Preserve these as distinct classification
and clause relationships. Verify the worker classification, applicable
award and dated salary schedule before choosing a ceiling.

Schedule 1.16 (printed page 96) identifies increment 5 as the top MPH-2
step. The annual amounts for the first full pay periods on or after
1 August 2025, 1 July 2026 and 1 July 2027 are AUD 148,041, 153,222 and
158,202 respectively. Record these dates as schedule triggers. An hourly
ceiling still requires the applicable payroll period start and salary
conversion basis, as well as the clause applicability decision above.

For a reviewed case, resolve the Schedule 1.16 trigger with
[`first_full_period`](../../docs/pay_period_effective.md) using the actual
contiguous payroll calendar. Use the resulting start to date the ceiling
only after confirming the agreement and award scope. Keep the annual
schedule value and reviewed hourly divisor as separate inputs. The
resolver and capped-overtime tests exercise these steps independently.

For medical scientists, the 2026 salary schedule lists the fifth MeS1
increment at AUD 89,764 from the first full pay period on or after
1 July 2026. Treat it as a candidate annual basis only if the Medical
Scientists Award clause 6.2.2 and the MS1-to-MeS1 mapping are confirmed
for the case. Clause 15 separately names MeS3 for the Salaried Employees
Interim Award provision it references. The two ceilings cannot be selected
from the pay schedule alone. The reviewed hourly conversion remains open.

The current capped API prices one local day at a time. The midnight
regression qualifies an explicit split with separately supplied daily
history and ceilings. For rounding qualification, retain the original
worked durations and obtain a payroll example showing whether the
quarter-hour rule applies to the daily total or separate bouts, how ties
are handled, and whether the minimum is evaluated before rounding.
The public historical text and scanned award evidence do not yet settle
that sequence for a current worker.

Clause 6.2.6 distinguishes ordinary overtime time off in lieu from the
public-holiday option. With agreement, the leave credit equals overtime
worked. For public-holiday overtime the clause allows that leave credit
with a separate cash payment at 1.5 times the applicable rate. A generic
cash-or-leave switch would omit that payment. Preserve the leave credit,
additional cash and already-counted base as separate quantities. Current
worker scope, payment basis and the application of the rounding/minimum
provisions to the public-holiday payment still need review.

For a separately verified public-holiday cash case, clause 6.2.2.4
provides a flat 2.5 multiplier. Represent that case as one tier starting
at zero. For an agreed time-off case, use the separate credit and cash
result. Classify the activity date before selecting either rule, and
reconcile the salary already counted in the base ledger. The historical
workbook percentage provides no evidence for that classification.

The synthetic flat holiday cash test prices four hours at a capped
AUD 40 hourly basis and a 2.5 multiplier. It returns AUD 400 with a
net adjustment of AUD 200 to the pre-counted base and no time credit.
All 11 capped-overtime tests passed.
