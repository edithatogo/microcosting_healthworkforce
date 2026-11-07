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
