from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
FIGURES_DIR = ROOT / "figures"
TABLES_DIR = ROOT / "tables"

RAW_CSV = DATA_DIR / "ray_benchmark_raw.csv"
SUMMARY_CSV = DATA_DIR / "ray_benchmark_summary.csv"

GRID = "uniform_grid"
TREE = "quadtree"
ALGORITHMS = (GRID, TREE)

COLORS = {
    GRID: "#2563eb",
    TREE: "#dc2626",
}
LABELS = {
    GRID: "Uniform Grid",
    TREE: "Quadtree",
}


def read_summary() -> list[dict]:
    rows: list[dict] = []
    with SUMMARY_CSV.open(newline="") as file:
        for row in csv.DictReader(file):
            parsed = dict(row)
            parsed["depth"] = int(row["depth"])
            parsed["cells_per_axis"] = int(row["cells_per_axis"])
            parsed["num_rays"] = int(row["num_rays"])
            parsed["seed"] = int(row["seed"])
            parsed["total_runtime_ns"] = int(row["total_runtime_ns"])
            parsed["avg_runtime_ns_per_ray"] = float(row["avg_runtime_ns_per_ray"])
            parsed["min_visited_partitions"] = int(row["min_visited_partitions"])
            parsed["max_visited_partitions"] = int(row["max_visited_partitions"])
            parsed["avg_visited_partitions"] = float(row["avg_visited_partitions"])
            parsed["total_visited_partitions"] = int(row["total_visited_partitions"])
            parsed["avg_runtime_ns_per_visited_partition"] = float(
                row["avg_runtime_ns_per_visited_partition"]
            )
            rows.append(parsed)
    return rows


def read_raw_grouped():
    runtimes = defaultdict(list)
    visited_counts = defaultdict(list)
    records_by_depth_ray = defaultdict(dict)

    with RAW_CSV.open(newline="") as file:
        for row in csv.DictReader(file):
            algorithm = row["algorithm"]
            depth = int(row["depth"])
            ray_id = int(row["ray_id"])
            runtime_ns = int(row["runtime_ns"])
            visited_count = int(row["visited_partition_count"])
            checksum = int(row["checksum"])

            key = (algorithm, depth)
            runtimes[key].append(runtime_ns)
            visited_counts[key].append(visited_count)
            records_by_depth_ray[(depth, ray_id)][algorithm] = {
                "visited_count": visited_count,
                "checksum": checksum,
                "runtime_ns": runtime_ns,
            }

    return runtimes, visited_counts, records_by_depth_ray


def save_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict], columns: list[str], labels: dict[str, str]) -> str:
    header = "| " + " | ".join(labels[column] for column in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row[column]) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def save_markdown_table(
    path: Path,
    rows: list[dict],
    columns: list[str],
    labels: dict[str, str],
    title: str,
) -> None:
    path.write_text(
        f"# {title}\n\n{markdown_table(rows, columns, labels)}\n",
        encoding="utf-8",
    )


def format_int(value: float | int) -> str:
    return f"{int(round(value)):,}"


def format_float(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}"


def prepare_tables(summary_rows, runtimes, visited_counts, records_by_depth_ray):
    by_algorithm_depth = {
        (row["algorithm"], row["depth"]): row for row in summary_rows
    }
    depths = sorted({row["depth"] for row in summary_rows})

    enriched_rows: list[dict] = []
    for depth in depths:
        grid = by_algorithm_depth[(GRID, depth)]
        tree = by_algorithm_depth[(TREE, depth)]
        speedup = tree["avg_runtime_ns_per_ray"] / grid["avg_runtime_ns_per_ray"]
        per_visit_ratio = (
            tree["avg_runtime_ns_per_visited_partition"]
            / grid["avg_runtime_ns_per_visited_partition"]
        )
        enriched_rows.append(
            {
                "depth": depth,
                "cells_per_axis": grid["cells_per_axis"],
                "avg_visited_partitions": format_float(
                    grid["avg_visited_partitions"], 2
                ),
                "grid_avg_ns_per_ray": format_int(grid["avg_runtime_ns_per_ray"]),
                "quadtree_avg_ns_per_ray": format_int(
                    tree["avg_runtime_ns_per_ray"]
                ),
                "quadtree_grid_runtime_ratio": format_float(speedup, 2),
                "grid_ns_per_visited_partition": format_int(
                    grid["avg_runtime_ns_per_visited_partition"]
                ),
                "quadtree_ns_per_visited_partition": format_int(
                    tree["avg_runtime_ns_per_visited_partition"]
                ),
                "quadtree_grid_per_visit_ratio": format_float(per_visit_ratio, 2),
            }
        )

    distribution_rows: list[dict] = []
    for algorithm in ALGORITHMS:
        for depth in depths:
            values = np.array(runtimes[(algorithm, depth)])
            visits = np.array(visited_counts[(algorithm, depth)])
            distribution_rows.append(
                {
                    "algorithm": algorithm,
                    "depth": depth,
                    "runtime_p50_ns": format_int(np.percentile(values, 50)),
                    "runtime_p90_ns": format_int(np.percentile(values, 90)),
                    "runtime_p99_ns": format_int(np.percentile(values, 99)),
                    "visited_p50": format_int(np.percentile(visits, 50)),
                    "visited_p90": format_int(np.percentile(visits, 90)),
                    "visited_p99": format_int(np.percentile(visits, 99)),
                }
            )

    agreement_rows: list[dict] = []
    for depth in depths:
        compared = 0
        count_mismatches = 0
        checksum_mismatches = 0
        runtime_deltas = []

        for (record_depth, _ray_id), algorithms in records_by_depth_ray.items():
            if record_depth != depth:
                continue
            if GRID not in algorithms or TREE not in algorithms:
                continue
            compared += 1
            grid = algorithms[GRID]
            tree = algorithms[TREE]
            if grid["visited_count"] != tree["visited_count"]:
                count_mismatches += 1
            if grid["checksum"] != tree["checksum"]:
                checksum_mismatches += 1
            runtime_deltas.append(tree["runtime_ns"] - grid["runtime_ns"])

        agreement_rows.append(
            {
                "depth": depth,
                "rays_compared": compared,
                "visited_count_mismatches": count_mismatches,
                "checksum_mismatches": checksum_mismatches,
                "median_extra_quadtree_runtime_ns": format_int(
                    np.percentile(runtime_deltas, 50)
                ),
            }
        )

    save_csv(
        TABLES_DIR / "summary_enriched.csv",
        enriched_rows,
        [
            "depth",
            "cells_per_axis",
            "avg_visited_partitions",
            "grid_avg_ns_per_ray",
            "quadtree_avg_ns_per_ray",
            "quadtree_grid_runtime_ratio",
            "grid_ns_per_visited_partition",
            "quadtree_ns_per_visited_partition",
            "quadtree_grid_per_visit_ratio",
        ],
    )
    save_csv(
        TABLES_DIR / "runtime_distribution_percentiles.csv",
        distribution_rows,
        [
            "algorithm",
            "depth",
            "runtime_p50_ns",
            "runtime_p90_ns",
            "runtime_p99_ns",
            "visited_p50",
            "visited_p90",
            "visited_p99",
        ],
    )
    save_csv(
        TABLES_DIR / "agreement_checks.csv",
        agreement_rows,
        [
            "depth",
            "rays_compared",
            "visited_count_mismatches",
            "checksum_mismatches",
            "median_extra_quadtree_runtime_ns",
        ],
    )

    save_markdown_table(
        TABLES_DIR / "summary_enriched.md",
        enriched_rows,
        [
            "depth",
            "cells_per_axis",
            "avg_visited_partitions",
            "grid_avg_ns_per_ray",
            "quadtree_avg_ns_per_ray",
            "quadtree_grid_runtime_ratio",
        ],
        {
            "depth": "Depth",
            "cells_per_axis": "Cells/Axis",
            "avg_visited_partitions": "Avg Visited",
            "grid_avg_ns_per_ray": "Grid ns/Ray",
            "quadtree_avg_ns_per_ray": "Quadtree ns/Ray",
            "quadtree_grid_runtime_ratio": "QT/Grid Runtime",
        },
        "Benchmark Summary",
    )
    save_markdown_table(
        TABLES_DIR / "agreement_checks.md",
        agreement_rows,
        [
            "depth",
            "rays_compared",
            "visited_count_mismatches",
            "checksum_mismatches",
            "median_extra_quadtree_runtime_ns",
        ],
        {
            "depth": "Depth",
            "rays_compared": "Rays",
            "visited_count_mismatches": "Count Mismatches",
            "checksum_mismatches": "Checksum Mismatches",
            "median_extra_quadtree_runtime_ns": "Median Extra QT ns",
        },
        "Agreement Checks",
    )

    return enriched_rows, distribution_rows, agreement_rows


def setup_figure():
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 200,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "font.size": 10,
            "axes.titleweight": "bold",
        }
    )


def plot_runtime(summary_rows):
    by_algorithm = defaultdict(list)
    for row in summary_rows:
        by_algorithm[row["algorithm"]].append(row)

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    for algorithm in ALGORITHMS:
        rows = sorted(by_algorithm[algorithm], key=lambda row: row["depth"])
        ax.plot(
            [row["depth"] for row in rows],
            [row["avg_runtime_ns_per_ray"] / 1_000 for row in rows],
            marker="o",
            linewidth=2.5,
            color=COLORS[algorithm],
            label=LABELS[algorithm],
        )

    ax.set_title("Average Traversal Runtime per Ray")
    ax.set_xlabel("Partition depth")
    ax.set_ylabel("Runtime per ray (microseconds)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "avg_runtime_per_ray.png")
    plt.close(fig)


def plot_runtime_log(summary_rows):
    by_algorithm = defaultdict(list)
    for row in summary_rows:
        by_algorithm[row["algorithm"]].append(row)

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    for algorithm in ALGORITHMS:
        rows = sorted(by_algorithm[algorithm], key=lambda row: row["depth"])
        ax.plot(
            [row["depth"] for row in rows],
            [row["avg_runtime_ns_per_ray"] / 1_000 for row in rows],
            marker="o",
            linewidth=2.5,
            color=COLORS[algorithm],
            label=LABELS[algorithm],
        )

    ax.set_yscale("log")
    ax.set_title("Average Traversal Runtime per Ray (Log Scale)")
    ax.set_xlabel("Partition depth")
    ax.set_ylabel("Runtime per ray (microseconds, log)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "avg_runtime_per_ray_log.png")
    plt.close(fig)


def plot_visited(summary_rows):
    by_algorithm = defaultdict(list)
    for row in summary_rows:
        by_algorithm[row["algorithm"]].append(row)

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    for algorithm in ALGORITHMS:
        rows = sorted(by_algorithm[algorithm], key=lambda row: row["depth"])
        ax.plot(
            [row["depth"] for row in rows],
            [row["avg_visited_partitions"] for row in rows],
            marker="o",
            linewidth=2.5,
            color=COLORS[algorithm],
            label=LABELS[algorithm],
        )

    ax.set_title("Average Visited Leaf Partitions per Ray")
    ax.set_xlabel("Partition depth")
    ax.set_ylabel("Visited partitions")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "avg_visited_partitions.png")
    plt.close(fig)


def plot_cost_per_partition(summary_rows):
    by_algorithm = defaultdict(list)
    for row in summary_rows:
        by_algorithm[row["algorithm"]].append(row)

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    for algorithm in ALGORITHMS:
        rows = sorted(by_algorithm[algorithm], key=lambda row: row["depth"])
        ax.plot(
            [row["depth"] for row in rows],
            [
                row["avg_runtime_ns_per_visited_partition"]
                for row in rows
            ],
            marker="o",
            linewidth=2.5,
            color=COLORS[algorithm],
            label=LABELS[algorithm],
        )

    ax.set_title("Average Runtime per Visited Partition")
    ax.set_xlabel("Partition depth")
    ax.set_ylabel("Nanoseconds per visited partition")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "runtime_per_visited_partition.png")
    plt.close(fig)


def plot_ratios(summary_rows):
    by_algorithm_depth = {
        (row["algorithm"], row["depth"]): row for row in summary_rows
    }
    depths = sorted({row["depth"] for row in summary_rows})
    per_visit_ratios = [
        by_algorithm_depth[(TREE, depth)]["avg_runtime_ns_per_visited_partition"]
        / by_algorithm_depth[(GRID, depth)]["avg_runtime_ns_per_visited_partition"]
        for depth in depths
    ]

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    ax.plot(
        depths,
        per_visit_ratios,
        marker="s",
        linewidth=2.5,
        color="#059669",
        label="Runtime per visited partition ratio",
    )
    ax.axhline(1.0, color="#111827", linewidth=1.0, linestyle="--")
    ax.set_title("Quadtree Cost Relative to Uniform Grid")
    ax.set_xlabel("Partition depth")
    ax.set_ylabel("Quadtree / Uniform Grid")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "quadtree_to_grid_ratios.png")
    plt.close(fig)


def plot_runtime_distributions(runtimes):
    depths = sorted({depth for _algorithm, depth in runtimes})
    positions = []
    values = []
    colors = []
    labels = []

    for depth_index, depth in enumerate(depths):
        base = depth_index * 3
        for offset, algorithm in enumerate(ALGORITHMS):
            positions.append(base + offset)
            values.append(np.array(runtimes[(algorithm, depth)]) / 1_000)
            colors.append(COLORS[algorithm])
        labels.append(base + 0.5)

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    box = ax.boxplot(
        values,
        positions=positions,
        widths=0.65,
        patch_artist=True,
        showfliers=False,
    )
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
        patch.set_edgecolor(color)
    for median in box["medians"]:
        median.set_color("#111827")
        median.set_linewidth(1.6)

    ax.set_xticks(labels)
    ax.set_xticklabels(depths)
    ax.set_title("Per-Ray Runtime Distribution")
    ax.set_xlabel("Partition depth")
    ax.set_ylabel("Runtime per ray (microseconds)")
    ax.legend(
        handles=[
            plt.Line2D([0], [0], color=COLORS[GRID], lw=8, alpha=0.55),
            plt.Line2D([0], [0], color=COLORS[TREE], lw=8, alpha=0.55),
        ],
        labels=[LABELS[GRID], LABELS[TREE]],
        frameon=False,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "runtime_distribution_boxplots.png")
    plt.close(fig)


def plot_visited_distributions(visited_counts):
    depths = sorted({depth for _algorithm, depth in visited_counts})
    values = [
        np.array(visited_counts[(GRID, depth)])
        for depth in depths
    ]

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    parts = ax.violinplot(
        values,
        positions=depths,
        widths=0.72,
        showmeans=True,
        showmedians=True,
        showextrema=False,
    )
    for body in parts["bodies"]:
        body.set_facecolor("#2563eb")
        body.set_edgecolor("#1d4ed8")
        body.set_alpha(0.45)
    parts["cmeans"].set_color("#111827")
    parts["cmedians"].set_color("#dc2626")

    ax.set_title("Distribution of Visited Partitions")
    ax.set_xlabel("Partition depth")
    ax.set_ylabel("Visited partitions per ray")
    ax.set_xticks(depths)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "visited_partition_distribution.png")
    plt.close(fig)


def plot_depth8_runtime_vs_visits(runtimes, visited_counts):
    depth = max(depth for _algorithm, depth in runtimes)
    fig, ax = plt.subplots(figsize=(8.8, 5.4))
    all_runtime_us = []

    for algorithm in ALGORITHMS:
        visits = np.array(visited_counts[(algorithm, depth)])
        runtime_us = np.array(runtimes[(algorithm, depth)]) / 1_000
        all_runtime_us.extend(runtime_us.tolist())
        ax.scatter(
            visits,
            runtime_us,
            s=11,
            alpha=0.18,
            color=COLORS[algorithm],
            label=LABELS[algorithm],
            edgecolors="none",
        )

    y_limit = np.percentile(np.array(all_runtime_us), 99)
    ax.set_ylim(0, y_limit * 1.08)
    ax.set_title(f"Runtime vs. Visited Partitions at Depth {depth} (Y Axis to p99)")
    ax.set_xlabel("Visited partitions")
    ax.set_ylabel("Runtime per ray (microseconds)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "depth8_runtime_vs_visited_partitions.png")
    plt.close(fig)


def make_plots(summary_rows, runtimes, visited_counts):
    setup_figure()
    plot_runtime(summary_rows)
    plot_runtime_log(summary_rows)
    plot_visited(summary_rows)
    plot_cost_per_partition(summary_rows)
    plot_ratios(summary_rows)
    plot_runtime_distributions(runtimes)
    plot_visited_distributions(visited_counts)
    plot_depth8_runtime_vs_visits(runtimes, visited_counts)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    summary_rows = read_summary()
    runtimes, visited_counts, records_by_depth_ray = read_raw_grouped()
    prepare_tables(summary_rows, runtimes, visited_counts, records_by_depth_ray)
    make_plots(summary_rows, runtimes, visited_counts)

    print(f"Wrote tables to {TABLES_DIR}")
    print(f"Wrote figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
