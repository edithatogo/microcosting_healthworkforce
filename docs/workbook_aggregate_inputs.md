# Historical aggregate inputs

The primary and WM sheets both use unweighted AVERAGE formulas for J34:U38.
The corresponding J40:U44 displays combine that mean with the observed MIN and
MAX across the five jurisdiction rows. The WM name alone does not make these
particular input cells weighted. Other weighted output tables retain their
separate mappings.

The profile labels mean input units using the original column meanings and
marks presentation strings as text. Currency, ordinary hours, annual leave and
fractions retain their distinct units. Blank base-year cells remain blank.
These are archived candidate summaries, with no statistical-interval or
individual-entitlement acceptance inferred from the displayed ranges.

The five jurisdiction summary display blocks in Sum Cost Jur link their C and
F columns to the same sheet's annual and hourly numeric bounds. Their strings
are labelled presentation text, while jurisdiction and personnel type retain
identity roles. The B69:B73 block contains personnel labels only and does not
supply cost observations. The mapping traces formulas without reinterpreting
archived lower and upper values as independently validated intervals.

The literal Sum Cost summary retains its reported strings and original header
wording; its values are not parsed into new unit prices. Medicare note regions
are contextual records. The historical system-change quantity and PSA reference
scalar explicitly retain unknown units and unresolved status. The transposed
personnel-header block carries identities only. None of these dispositions
promotes contextual notes, labels or an archived scalar to an accepted parameter.

Four weighted aggregate placeholder blocks and the DSA archived jurisdiction/
personnel columns carry identity roles only. The isolated AK39 zero retains
an unresolved historical-value role with no declared economic unit. Recording
that literal zero does not supply a missing lower-bound input in AK34.
The formula reference audit found no dependencies on AK39. Neither
sheet-local defined name targets that cell, and the workbook contains
no external-link parts. Keep the literal outside costing inputs while
retaining its original value and coordinate.

On the WM sheet, Y52:Y56 and AB52:AB56 format the weighted annual and hourly
numeric results from rows 46:50. The component displays J95:X99 and J144:X148
instead retain unweighted input AVERAGE/MIN/MAX formulas and first-jurisdiction
salary/denominator references. The mapping keeps these distinct formula bases;
a WM sheet title does not establish that every displayed quantity is weighted.

DSA component displays in rows 83:87 and 120:124 are presentation text.
Their mean and observed bounds use the DSA input columns, first-jurisdiction
salary AS, annual-cost denominator AV for shares, and annual-leave scaling by
52. The archived component proxy arithmetic remains distinct from an accepted
leave, loading or payroll rule.

The DSA aggregate input/output presentation in rows 40:44 has 35 display
columns: 12 format input means with observed jurisdiction minima/maxima, and
23 format salary or scenario-bound triples. Their references are retained
explicitly. The two bound conventions remain separate; neither is promoted to
an independently validated statistical interval.

The six DSA publication sections distinguish formula-linked identities and
formatted bounds, stored literal display strings, jurisdiction presentation
columns, and mixed archival layouts below the main numeric block. Unknown-unit
or mixed historical values retain no economic unit. Formula displays keep their
source links, including archived mean/95% CI labels; those labels do not establish
statistical validity. Layout fragments remain contextual or unresolved records.

The PSA Validation sheet labels A2 as an expected mean cost. A2 is a
numeric literal with no explicit formula references from other sheets
in the pinned workbook. The label does not identify the unit, weighting
or generating model. Retain it as a historical reference pending
provenance for those fields.

No numeric cell on another sheet in the private recalculation matched
A2 within an absolute difference of 0.00000001. This comparison checks
individual cells. The scalar's generating calculation remains unknown.

Git commit `8bb90f9` introduced the validation sheet on 5 August 2025.
Its validator compared A2 with the unweighted mean of the supplied
PSA result rows' `mean_cost` values. That establishes the original
comparison method in the code. The commit does not identify how A2
was generated or substantiate the comparison's scientific assumptions.

The scalar matches its value in the introducing commit. Git history
on the current branch records no subsequent edits to the workbook.
Treat the scalar as evidence from that historical validation setup
when comparing it with later analysis code.
