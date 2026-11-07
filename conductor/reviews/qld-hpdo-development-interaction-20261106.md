# Queensland practitioner development allowance interaction — 6 November 2026

The retained [Health Practitioners and Dental Officers (Queensland Health)
Certified Agreement No. 4 of 2022](https://www.qirc.qld.gov.au/sites/default/files/2023-06/2023_cb43.pdf),
SHA-256 `33cbcde611bdced6eae000cb21417a11960964259eb76bd3e19c9f0265f06b3a`,
was certified and became operative on 26 May 2023. The certificate records a
subsequent wage-schedule amendment. Clause 6.2.1, PDF page 31, lists category
amounts from 17 October 2022, 2023 and 2024; those dates must not be confused
with the agreement's certification or operation date.

Clause 6.2.2 states that the allowance is paid in fortnightly salary, continues
during paid leave, and is excluded from calculating leave loading, penalty
rates, overtime and superannuation. Clause 6.2.3 provides a pro-rata entitlement
for permanent part-time practitioners and dental officers working at least
15.2 hours per fortnight; clause 6.2.4 describes a separate service threshold
for temporary staff. Category identification refers to HR Policy C42. The
table itself does not explicitly state the period represented by its amounts;
fortnightly payment frequency alone does not settle that unit. Verify the
applicable policy, category, appointment, service, actual dates and later
variations before creating an accepted condition.

## Policy example and payment basis

The retained [HR Policy C42 dated 11 October 2024](https://www.health.qld.gov.au/__data/assets/pdf_file/0037/395893/qh-pol-146.pdf),
SHA-256 `d20a16570c0af9d82e5bff961d661a78198c3238a1420101649809fe5c61d770`,
reproduces the agreement's category A, B and C amounts on PDF page 2. Its
worked example on page 4 uses the 17 October 2023 category C amount of $1,975
as a full-time annual basis: 30.4/76 produces $790 per annum and the example
states $30.38 per fortnight. Thus that specific table entry's annual basis is
supported by a published example. The shared table suggests the same basis for
other entries, but those individual cells have not been independently traced to
an explicit example. The 2024 policy's retrospective description is not proof
of an earlier policy edition, an employee's eligibility or an individual payment.
A private successor candidate extraction records this one supported unit and
its policy-page lineage; the other eight units remain unverified, and the
agreement's `other` to policy category C association remains a candidate.

Policy section 1.4 bases part-time proportion on ordinary hours including paid
leave. Section 1.1 says half-pay leave receives the allowance at 50%. The
separate [11 October 2024 guideline](https://www.health.qld.gov.au/__data/assets/pdf_file/0027/731196/qh-gdl-146-1.pdf),
SHA-256 `fdaf8818e2448c2298a909b6db0bf3e46d55ecdaac8d5490711078307d36dd72`,
section 4 on PDF page 5 discusses allowance accrual, including half-pay leave,
and excludes unpaid leave and overtime from accrual. Accrual and payment are
different events; do not replace one with the other or assume that a simple
hourly increment prices all leave cases. Category D and location-specific
eligibility require their own source and date review.

The current synthetic derived schedule can represent an expressly selected
allowance without an incremental superannuation rule. A focused test compares
that case with an explicitly added incremental rule and checks the difference
without double-counting base salary superannuation. This validates a software
interaction, not the source's real-world scope or the full leave, penalty and
overtime exclusions. Other table-entry units, paid-leave allocation, thresholds and
effective-date decisions remain unresolved; no historical rate is promoted.

## Profession-specific location categories

The 11 October 2024 policy's facility tables distinguish health practitioners
(Attachment 2, PDF page 11) from dental officers (Attachment 3, PDF page 16).
Visual inspection confirms that, within Cairns and Hinterland, Dimbulah is
category D for health practitioners but A for dental officers; Chillagoe is D
for health practitioners but B for dental officers. Cairns and Gordonvale are
category C in both tables. The HP table matches D to designated remote nursing
locations; the dental table has categories A–C. The policy separately states
minimum hours and temporary-service conditions. These examples qualify dated
table mappings, not an individual's entitlement, another edition, the unit of
each amount, or a current category after amendments. Never use a location-only
category lookup across both professional streams.

A private, versioned candidate extraction now records all Cairns and Hinterland
entries on these two pages: 20 health-practitioner and 19 dental-officer
facility/category rows. The generator verifies the held policy SHA-256, unique
stream/facility keys and the Dimbulah difference. Cow Bay appears in the HP
table but not the dental table; the extraction leaves the latter unknown rather
than asserting ineligibility. The candidate JSON is
`.private-runs/workforce-source-coverage-20261106/qld-c42-cairns-categories-2024-candidate-v1.json`,
SHA-256 `b6bd916f2f73b393510761f84370ba3bb0d84c4c7c78e11a672848cade674137`.
Its issue date is not a proven effective interval, and these 39 records do not
cover other health services or determine worker eligibility.

The versioned successor
`.private-runs/workforce-source-coverage-20261106/qld-c42-regional-categories-2024-candidate-v2.json`
preserves those 39 rows and adds all Central Queensland and Central West
facility entries shown on the same two visually inspected pages: 41 and 26
rows respectively, for 106 total. Its SHA-256 is
`83b796879f387cf533263afc657085eace4e25928c2d7dd38604937ee56a6212`;
the generator retains the predecessor hash, checks unique service/stream/
facility keys and confirms that Capella is HP category D and dental category B.
This remains a partial policy extraction: other services and pages, policy
periods, worker eligibility and current validity are not established.

The next private successor,
`.private-runs/workforce-source-coverage-20261106/qld-c42-regional-categories-2024-candidate-v3.json`,
preserves all 106 earlier rows and adds 93 entries visually checked against PDF
pages 12 and 17, for 199 candidates. Added rows cover Darling Downs, Mackay,
selected Gold Coast, Metro North and Metro South entries, and dental-officer
entries for North West. The HP table lists Taroom and Wandoan as D while the
dental table lists them as B. The dental Mackay Whitsunday (Cannonvale) text
appears in the A column without a bullet; its row carries a source-formatting
qualification rather than an unqualified item boundary. The successor SHA-256
is `fa24f2ac32fb926df0787b1f92f35a36107e4bb96a2899abe830ef1594674646`.
Other pages, omitted streams, effective intervals and individual eligibility
remain unassessed; absence from this partial file is not ineligibility.

Version 4,
`.private-runs/workforce-source-coverage-20261106/qld-c42-regional-categories-2024-candidate-v4.json`,
adds 147 entries and preserves the 199 predecessor rows, yielding 346 candidate
facility entries across all nine attachment pages 11–19. The remaining five
pages were visually checked. A separate page-by-page bullet count reconciles:
page 11 has one empty bullet; page 12 has one bullet for a Department of
Health eligibility note rather than a facility; page 17 has one unbulleted
Whitsunday entry already flagged for source-format clarification. All other
page bullet counts match row counts. Literal naming differences such as
`Mount Perry` and `Mt Perry` are retained; they have not been normalised into
assumed facility identities. SHA-256:
`9aed12ea15f1ea7573f5d0058307f2915504647c1314a236367e44b09ebb864f`.
This completes a transcription candidate for these two historical tables, not
independent acceptance, a policy effective interval, later amendments, worker
eligibility, or nationwide source coverage.

## Currency check — 6 November 2026

The official C42 URL returned byte-identical 11 October 2024 policy PDF content
on this date; both files have SHA-256
`d20a16570c0af9d82e5bff961d661a78198c3238a1420101649809fe5c61d770`.
This establishes what that URL served, not a complete amendment search or each
facility's current eligibility. Queensland Health's [bargaining status page](https://www.careers.health.qld.gov.au/working-for-us/awards-agreements-and-orders/enterprise-bargaining-agreement),
updated October 2026, states HPDO5 arbitration is continuing and HPDO4 terms
continue while it proceeds. Its [health practitioner wage page](https://www.health.qld.gov.au/hrpolicies/salary/health-practitioners)
separately states 2025 and 2026 State Wage Case award rates apply where higher
than HPDO4 rates. Do not apply the historical agreement salary schedule as
current without the relevant award comparison. This wage statement does not
establish a new PDA amount, a facility's entitlement or the arbitration outcome.
