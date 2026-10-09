"""Render the published cross-task communication summaries as three panels."""

import argparse
import json
from pathlib import Path

from analysis import compare_profiles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).parent / "data/results.json")
    parser.add_argument("--output", type=Path, default=Path("cross-task.pdf"))
    args = parser.parse_args()
    data = json.loads(args.data.read_text())
    compare_profiles(data)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    tasks = list(dict.fromkeys(row["task"] for row in data["cross_task"]))
    by_key = {(row["task"], row["profile"]): row for row in data["cross_task"]}
    profiles = [("Raw", "#7A7A7A"), ("Full", "#4C78A8"), ("NSPR-8", "#E07A5F")]
    metrics = [("traffic_mib", "Traffic (MiB/round)"),
               ("critical_mean_ms", "Critical path (ms)"), ("success_pct", "Success (%)")]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "pdf.fonttype": 42, "svg.fonttype": "none"})
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.7), layout="constrained")
    for ax, (metric, title) in zip(axes, metrics):
        for index, (profile, color) in enumerate(profiles):
            rows = [by_key[task, profile] for task in tasks]
            values = [row[metric] for row in rows]
            error = None
            if metric == "critical_mean_ms":
                error = [[0] * len(rows), [row["critical_p95_ms"] - row[metric] for row in rows]]
            ax.bar([i + (index - 1) * .24 for i in range(len(tasks))], values,
                   width=.22, color=color, label=profile, yerr=error,
                   error_kw={"elinewidth": .8, "capsize": 2, "ecolor": "#444444"})
        ax.set_xticks(range(len(tasks)), [task.replace(" ", "\n") for task in tasks])
        ax.set_ylabel(title)
        ax.set_ylim(bottom=0, top=105 if metric == "success_pct" else None)
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.grid(axis="y", alpha=.18)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside upper center", ncol=3, frameon=False)
    fig.savefig(args.output, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
