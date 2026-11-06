# Explicit salary inclusions

An accepted salary condition can declare `included_components`, naming cost
components already included in that salary. The salary's source, citation, scope
and effective interval must support each declared inclusion. The library does
not infer inclusions from an instrument title or rate.

A release rejects a separate condition with a matching component when its
interval overlaps the salary. Derived snapshot and activity costing also reject
a selected derived rule whose component matches an active inclusion. Adjacent,
non-overlapping editions remain possible. Existing releases with no declared
inclusions retain their original canonical release hashes; a nonempty assertion
is included in the new release hash.

Names must be chosen consistently by the caller: the guard cannot detect an
undeclared inclusion, a synonym, an overlapping external ledger, or an
unmodelled industrial rule. A declaration does not determine employer,
classification, effective date or individual eligibility. In particular, a
source-specific bundled salary must not be substituted into a different model
without reviewing all included amounts and applicable terms.
