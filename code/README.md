# VLA-Fabric Code

Analysis tools accompanying **VLA-Fabric: Communication-Efficient Coordination
for Scalable Networks of VLA Agents**.

## Contents

- [Communication and paired-outcome analysis](analysis.py)
- [Cross-task plotting](plot_results.py)
- [Evaluation results and protocols](EVALUATION.md)
- [Machine-readable cross-task results](data/results.json)
- [Download the tools and supporting data](../assets/downloads/vla-fabric-tools.zip)

## Communication Results

The included summary reproduces the cross-task screening comparison in Figure 5.
Compute traffic reduction, critical-path reduction, and success-rate change:

```bash
python analysis.py profiles
python analysis.py profiles --reference Full --candidate NSPR-8
```

The analysis uses only the Python standard library. Traffic is bidirectional
payload in MiB per planning round. Success uses paired-200 evaluations;
critical-path mean and P95 use separate strict timing-50 evaluations. P95 is
a latency percentile, not a confidence interval. Do not combine these results
with the preprocessing sweep or screening-search aggregate.

## Paired Outcomes

Provide two CSVs with `condition_id,success` columns, where success is `0` or `1`:

```bash
python analysis.py paired reference.csv candidate.csv
```

The utility rejects duplicate IDs, mismatched condition sets, and invalid
outcomes instead of silently dropping or treating unresolved trials as failures.
Matched IDs alone do not establish a paired protocol; observations, seeds, and
evaluation settings must also match.

## Figures

With Matplotlib 3.7 or later available:

```bash
python plot_results.py --output cross-task.pdf
python plot_results.py --output cross-task.svg
```

The chart reports success, traffic, and critical-path mean; latency whiskers
extend to P95. Source values are in `data/results.json`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License

The utilities are provided under the MIT license in `LICENSE`.

This release includes communication-analysis and evaluation utilities.
Additional implementation components will be released progressively.
