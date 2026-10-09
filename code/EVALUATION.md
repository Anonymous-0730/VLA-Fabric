# Evaluation Results

Supporting results for **VLA-Fabric: Communication-Efficient Coordination for
Scalable Networks of VLA Agents**. See the [paper](../assets/paper/vla-fabric-paper.pdf)
for the methods, citations, and experimental discussion.

## Task Capability

Success rates are percentages. VLA-Fabric uses Full communication. TwinVLA is
the bimanual reference; RoboFactory Diffusion Policy (DP) results use 150
demonstrations and are reported in RoboFactory. These comparisons use the
respective evaluation protocols documented in the paper; they are not paired
comparisons between VLA-Fabric and the reference policies.

| Arms | Task | Reference policy | Reference (%) | VLA-Fabric (%) |
| ---: | --- | --- | ---: | ---: |
| 2 | Handover Box | TwinVLA | 76.0 | 75.0 |
| 2 | Shoes Table | TwinVLA | 83.0 | 78.0 |
| 2 | Handover Mic | TwinVLA | 94.5 | 81.5 |
| 3 | Camera Alignment | RoboFactory DP | 19.0 | 100.0 |
| 3 | Stack Cube | RoboFactory DP | 22.0 | 75.0 |
| 4 | Take Photo | RoboFactory DP | 20.0 | 96.5 |

Handover Box and Shoes Table use ALOHA; Handover Mic uses RoboTwin. Camera
Alignment, Stack Cube, and Take Photo use RoboFactory.

With one agent, the organization reduces to a local SingleVLA policy, without
inter-agent communication. The following LIBERO success rates are reported by
TwinVLA, cited in the paper; they are not new experiments in this release.

| LIBERO suite | SingleVLA success (%) |
| --- | ---: |
| Spatial | 92.4 |
| Object | 94.5 |
| Goal | 93.5 |
| Long | 63.7 |

## Communication Ablations

These fixed-weight inference ablations use paired-200 evaluations for each
task. Only inference communication changes; the policy is not retrained.
Disabling private K/V alone is not the same as disabling all communication.

| Communication | Handover Box (%) | Shoes Table (%) | Handover Mic (%) | Stack Cube (%) |
| --- | ---: | ---: | ---: | ---: |
| Full | 75.0 | 78.0 | 81.5 | 75.0 |
| No Common | 38.5 | 19.0 | 52.5 | 66.0 |
| No Private K/V | 59.0 | 64.5 | 60.5 | 50.0 |
| Random Private K/V | 62.5 | 37.5 | 54.0 | 0.0 |
| No Action | 43.0 | 7.5 | 52.5 | 29.0 |
| Random Action | 31.0 | 17.0 | 66.0 | 26.5 |
| No communication | 20.0 | 1.5 | 13.5 | 2.0 |

## Cross-Task Communication

The machine-readable values are in [data/results.json](data/results.json).
The homepage charts use the same source. This comparison is separate from
the task-capability and message-ablation evaluations above; do not substitute
success rates between cohorts, even when profile names match.

- **Raw:** the direct operator-level common-path interface, with 24 active layers.
- **Full:** the all-layer hidden workspace, with 24 active layers.
- **NSPR-8:** the hidden workspace with the fixed synchronization mask
  `{0, 2, 4, 10, 16, 18, 20, 22}`, without task-specific rescreening.

All three profiles retain private K/V and action-intent communication. Raw and
Full aggregate at different computational boundaries: Raw is not a task-success
upper bound for Full or NSPR-8.

Traffic is bidirectional payload in **MiB per planning round** (1 MiB = 2^20
bytes). Success uses **paired-200** evaluations. Communication critical-path
mean and P95 use separate CUDA-synchronized **strict timing-50** evaluations.
Timing-run success counts do not replace the paired-200 success rates. P95 is
a latency percentile, not an error bar on the mean or a confidence interval.

| Task | Profile | MiB/round | Critical-path mean (ms) | P95 (ms) | Success (%) |
| --- | --- | ---: | ---: | ---: | ---: |
| Handover Box | Raw | 148.877 | 270.793 | 336.478 | 72.0 |
| Handover Box | Full | 34.268 | 106.323 | 129.737 | 70.0 |
| Handover Box | NSPR-8 | 16.440 | 78.252 | 100.332 | 68.5 |
| Shoes Table | Raw | 151.063 | 247.157 | 340.195 | 72.0 |
| Shoes Table | Full | 34.695 | 102.146 | 113.468 | 80.0 |
| Shoes Table | NSPR-8 | 16.594 | 78.690 | 100.937 | 71.0 |
| Camera Alignment | Raw | 228.465 | 404.970 | 442.909 | 100.0 |
| Camera Alignment | Full | 52.859 | 124.428 | 144.195 | 100.0 |
| Camera Alignment | NSPR-8 | 25.543 | 93.950 | 107.804 | 99.0 |
| Take Photo | Raw | 310.785 | 626.647 | 650.330 | 77.5 |
| Take Photo | Full | 71.723 | 180.329 | 196.171 | 96.5 |
| Take Photo | NSPR-8 | 34.535 | 126.195 | 141.818 | 97.5 |

## Analysis

Run the included standard-library utilities from this directory:

```bash
python analysis.py profiles
python analysis.py profiles --reference Full --candidate NSPR-8
python analysis.py paired reference.csv candidate.csv
```

The paired command expects matching `condition_id,success` CSV records, with
binary success values. It validates IDs and outcomes but does not validate the
underlying experimental protocol. See the [README](README.md) for plotting
and tests.
