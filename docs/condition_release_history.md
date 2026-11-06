# Knowledge-dated condition releases

`ConditionHistory` stores a caller-reviewed linear series of full condition
releases for one jurisdiction, employer, classification and costing method.
Each edition has a unique release ID, a `known_from` date and, after the first,
the identity it supersedes. Knowledge dates must increase. These are explicit
modeller assertions; the library does not infer a decision's publication date,
worker eligibility, pay-period applicability or the current industrial instrument.

Select an edition with `history.select(knowledge_date)` and use the returned
release in the existing static or dynamic condition costing methods. Their work
date and effective-date validation remain separate from the knowledge date.
Selection returns a pin containing the release ID, knowledge date and SHA-256 of
canonical serialized release content. Preserve the pin with the result; `replay`
checks that the edition was known then and that its complete content still
matches. A changed edition must have a new release ID and must not rewrite a
previous pin. An unknown or unverified source still cannot be priced through a
condition release.

When a release has a fixed `as_known_at` date, its edition cannot be declared
known before that date. Retrospective conditions require reviewed entitlement
intervals, a matching release knowledge date and source scope and hash checks.
They do not establish legal entitlement or payment timing. Adding these fields
changes serialized release content and therefore its pin hash; retain older
versioned code and original releases for replay of previously issued pins.

This initial contract supports a linear history for one scope. It does not
model parallel interpretations, automatic source acquisition, legal pay-period
application, backpay or cash timing, or a complete source acceptance process.
