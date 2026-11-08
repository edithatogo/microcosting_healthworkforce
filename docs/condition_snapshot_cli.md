# Condition snapshot CLI

Run `python -m src.conditions_cli --release release.json --snapshot snapshot.json
--output result.json` with the selected repository interpreter. The snapshot
JSON contains `{"as_of":"2026-06-01","hours":"2"}`. The supplied release must
pass the same source and condition validation as the static library API.

The result retains release, method, classification, date, component amounts,
exact total and source condition details. Output creation refuses an existing
file. Activity costing uses `--activity activity.json --timezone UTC` instead;
the two input modes are mutually exclusive. Snapshot hours represent nominal
paid hours; capacity, overtime and leave cover need their explicit methods.

## Productive capacity and replacement cover

Use `microcosting-healthworkforce-v2 --release release.json --capacity capacity.json --output result.json`
to price a single annual capacity scenario. Supply the valuation date and
explicit, nonoverlapping loss and cover assumptions.

```json
{
  "as_of": "2026-06-01",
  "losses": [{"loss_id": "leave", "hours": "200"}],
  "cover_hours": "100",
  "cover_hourly_cost": "60",
  "losses_disjoint": true
}
```

The result reports paid cost, incremental cover, productive hours for the
original worker, exact cost fractions and the original assumptions. Choose
one request mode. The output path must be new.

## Attach reviewed workbook provenance

For a single release, pass `--workbook-origins origins.json` to attach
reviewed workbook origins before pricing. The JSON object is keyed by
condition ID. Each value supplies `workbook_sha256`, `sheet`,
`coordinate`, `applicability`, and `review_evidence`.

The mapped condition must already have an accepted release and a
verified instrument source. Workbook applicability must also be
`verified`. An unknown condition ID, conflicting existing provenance
or unresolved applicability prevents output creation. Retain the
reviewed mapping with the release evidence. Assignment timelines
carry provenance inside their pinned releases.

## Roster overtime

Run `microcosting-healthworkforce-v2 --release release.json --roster roster.json --output result.json`
with one worker and one reviewed overtime rule. The roster JSON has four
fields.

- `period` supplies `starts_at`, `ends_at`, `history_through`, `prior_hours`
  and `history_complete`. Use timezone-aware instants and end the prior
  history exactly at the first supplied activity.
- `rule` supplies the reviewed threshold, salary multiplier, source ID and
  SHA-256, citation and effective interval. Use the applicable rule for
  the worker and period.
- `activities` supplies all eligible activities from the history boundary
  through the period end, with one resource per activity and no overlap.
- `timezone` supplies the IANA timezone for condition dates.

The output records ordinary and overtime hours, the exact cost and
premium fractions, and the condition and rule lineage for each segment.
At AUD 50 per hour, a two-hour shift beginning with 39 eligible hours
against a 40-hour threshold and a 1.5 multiplier costs AUD 125.
