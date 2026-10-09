"""Analyze communication profiles and strictly matched binary rollout outcomes."""

import argparse
import csv
import json
import math
from pathlib import Path


def compare_profiles(data, reference="Raw", candidate="NSPR-8"):
    groups = {}
    for row in data["cross_task"]:
        profiles = groups.setdefault(row["task"], {})
        if row["profile"] in profiles:
            raise ValueError(f"Duplicate task/profile: {row['task']}, {row['profile']}")
        for field in ("traffic_mib", "critical_mean_ms", "success_pct"):
            value = row[field]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {field}: {value}")
        if row["success_pct"] > 100:
            raise ValueError("Success must be a percentage in [0, 100]")
        profiles[row["profile"]] = row
    results = []
    for task, profiles in groups.items():
        if reference not in profiles or candidate not in profiles:
            raise ValueError(f"Missing reference or candidate for {task}")
        ref, cand = profiles[reference], profiles[candidate]
        if ref["traffic_mib"] <= 0 or ref["critical_mean_ms"] <= 0:
            raise ValueError("Reduction requires a positive reference")
        results.append({
            "task": task,
            "reference": reference,
            "candidate": candidate,
            "traffic_reduction_pct": 100 * (1 - cand["traffic_mib"] / ref["traffic_mib"]),
            "critical_path_reduction_pct": 100 * (1 - cand["critical_mean_ms"] / ref["critical_mean_ms"]),
            "success_change_pp": cand["success_pct"] - ref["success_pct"],
        })
    return results


def read_outcomes(path):
    outcomes = {}
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not {"condition_id", "success"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV requires condition_id and success columns")
        for row in reader:
            identity = (row["condition_id"] or "").strip()
            value = (row["success"] or "").strip()
            if not identity or identity in outcomes:
                raise ValueError("Missing or duplicate condition_id")
            if value not in ("0", "1"):
                raise ValueError("Success must be 0 or 1; exclude unresolved/error trials explicitly")
            outcomes[identity] = value == "1"
    return outcomes


def paired_summary(reference, candidate):
    if not reference or reference.keys() != candidate.keys():
        raise ValueError("Paired outcomes require identical nonempty condition ID sets")
    if any(type(v) is not bool for v in [*reference.values(), *candidate.values()]):
        raise ValueError("Paired outcomes must be Boolean")
    counts = dict(both_success=0, reference_only=0, candidate_only=0, both_fail=0)
    names = {(True, True): "both_success", (True, False): "reference_only",
             (False, True): "candidate_only", (False, False): "both_fail"}
    for identity in reference:
        counts[names[reference[identity], candidate[identity]]] += 1
    n = len(reference)
    return {"trials": n, **counts,
            "reference_success_pct": 100 * sum(reference.values()) / n,
            "candidate_success_pct": 100 * sum(candidate.values()) / n,
            "success_change_pp": 100 * (counts["candidate_only"] - counts["reference_only"]) / n}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    profiles = sub.add_parser("profiles", help="Compare matched communication profiles")
    profiles.add_argument("--data", type=Path, default=Path(__file__).parent / "data/results.json")
    profiles.add_argument("--reference", default="Raw")
    profiles.add_argument("--candidate", default="NSPR-8")
    paired = sub.add_parser("paired", help="Summarize matched rollout CSVs")
    paired.add_argument("reference", type=Path)
    paired.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        result = (compare_profiles(json.loads(args.data.read_text()), args.reference, args.candidate)
                  if args.command == "profiles"
                  else paired_summary(read_outcomes(args.reference), read_outcomes(args.candidate)))
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
