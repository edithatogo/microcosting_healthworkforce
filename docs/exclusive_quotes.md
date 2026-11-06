# Exclusive quoted allowances

`src.exclusive_quotes.price_exclusive_quotes` validates a source-reviewed group
of alternative components and prices one caller-selected quote per explicit
resource exposure window. It accepts one or several dated windows, so the same
contract supports snapshot and dynamic allocations. The output retains the rule,
original case evidence and an exact `price_units` ledger.

Supply an `ExclusiveQuoteRule` with at least two distinct component names, a unit,
local timezone, held policy source/hash/citation, reviewed interpretation, scope,
operative dates and knowledge date matching the quote release. Each
`ExclusiveQuoteAllocation` supplies resource/identity, aware start/end instants,
a valuation date within the local window, chosen quote and explicit quantity.
Eligibility, complete relevant history, context-selection basis and dated evidence
are required. Assumed case inputs or policy interpretation mark the result as a
scenario. An observed complete-window assertion cannot predate that window.

The function rejects overlapping windows for the same resource within the call,
including different IDs or alternative quotes. Adjacent half-open windows and
simultaneous windows for different resources are allowed. A selected quote must
belong to the group, use the same unit and cover the entire local-date window.
Both ends require policy/source coverage. Split a price or policy change into
explicit non-overlapping windows; the function does not infer quantity allocation.

A known zero retains a qualified row. An empty set or unknown eligibility/history
is rejected. Inputs are revalidated, including instances modified with unchecked
`model_copy`. Exact fractions do not depend on Decimal context precision.

This validates supplied allocations. Geography, entitlement, proration, highest
amount selection, salary/overtime bases and whole-period caps require their own
source-qualified methods. In particular, non-overlap does not enforce a rolling
24-hour on-call allowance cap: two adjacent short windows might still belong to
one entitlement. The caller must qualify the window convention before using such
units. No cross-call duplicate detection or automatic combination with salary,
recall, tax, superannuation or other cost ledgers is performed. Public tests use
fictional prices and policy data; they do not establish actual award applicability.
