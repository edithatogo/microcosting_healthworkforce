# Conditional PSA precision diagnostic — 6 November 2026

The existing 10,000-draw simulation was reviewed without changing or rerunning
the model. The saved `simulation.parquet` SHA-256 matched the recorded finished
receipt (`95d11af8224c67bba73b8db96305b48929ea4267e03c9313051bb33007d3bed1`);
all 10,000 cost values were finite. The run uses the existing 20261103 seed,
legacy input distributions, independent parameter draws shared across rows,
and the equal-weight mean of the 25 prepared workforce rows.

For each population percentile of the conditional simulation distribution,
the table reports an individual approximate 95% distribution-free order-statistic
interval. Ranks are selected conservatively using the 2.5% and 97.5% quantiles
of the appropriate Binomial(10000, p) count, with one-based endpoints. The
point estimate uses the existing linear interpolation convention. These are
Monte Carlo precision intervals for the estimated percentile, not confidence
intervals for workforce costs or scientific model validity.

| Conditional percentile | Estimate | Monte Carlo interval | Half-width / estimate |
|---|---:|---:|---:|
| 2.5% | 296441.32 | 296293.62–296606.96 | 0.0529% |
| 97.5% | 326695.25 | 326555.59–326883.89 | 0.0502% |

The simulated mean is 311177.02 and its sample-standard-deviation-based Monte
Carlo standard error is 90.93, conditional on the same model. The two tail
intervals are individual intervals, not a simultaneous 95% band. Results assume
independent simulation iterations; they do not address parameter or model
misspecification. The binomial rank calculation used the exact probability
recurrence rather than resampling, and the recorded values are rounded only
for display.

No numerical precision target has been specified, so these measurements do not
establish that precision is sufficient. The absolute productive-time prior has
support above one despite the workbook's fraction interpretation; the source
and support of all priors, dependence, row sharing, intended weights and
estimand remain unapproved. The 150000 scalar is not the original workbook
midpoint reference. No parameter, seed, input or prior was changed. Conditional
computational qualification remains distinct from scientific acceptance.
