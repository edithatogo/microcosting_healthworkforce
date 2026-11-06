# Candidate source links

`link_held_candidates` attaches explicit, reasoned associations between a
screening target and a held source edition in a validated `SourceRegistry`.
It checks target identity, source identity, held status, jurisdiction and
duplicate links. Existing discovery leads and candidate links are retained.

These associations do not establish occupation, sector or employer coverage,
worker eligibility, operative dates or industrial precedence. Every linked gap
remains `applicability_unassessed`; source bytes and their hashes must be
verified independently before relying on a holding assertion. A candidate link
does not promote a `SourceRecord` or create an accepted condition release.
