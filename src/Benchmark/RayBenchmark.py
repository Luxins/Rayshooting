from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns

from BasicGeometry.BasicGeometry import AABB, Vec2, square_bounds_from_aabb
from Ray.Ray import Ray
from SpatialPartitioners.Quadtree.Quadtree import Quadtree
from SpatialPartitioners.UniformGrid.UniformGrid import UniformGrid, VisitedCell


DEFAULT_DEPTHS = (2, 3, 4, 5, 6, 7, 8)
DEFAULT_NUM_RAYS = 10_000
DEFAULT_SEED = 42
DEFAULT_WORLD_BOUNDS = AABB(Vec2(0.0, 0.0), Vec2(1.0, 1.0))

RAW_COLUMNS = [
    "algorithm",
    "depth",
    "cells_per_axis",
    "ray_id",
    "origin_x",
    "origin_y",
    "direction_x",
    "direction_y",
    "visited_partition_count",
    "runtime_ns",
    "checksum",
]

SUMMARY_COLUMNS = [
    "algorithm",
    "depth",
    "cells_per_axis",
    "num_rays",
    "seed",
    "total_runtime_ns",
    "avg_runtime_ns_per_ray",
    "min_visited_partitions",
    "max_visited_partitions",
    "avg_visited_partitions",
    "total_visited_partitions",
    "avg_runtime_ns_per_visited_partition",
]

CHECKSUM_OFFSET = 1469598103934665603
CHECKSUM_PRIME = 1099511628211
CHECKSUM_MASK = (1 << 64) - 1


@dataclass(frozen=True)
class BenchmarkFiles:
    raw_csv: Path
    summary_csv: Path


def parse_depths(value: str) -> list[int]:
    depths: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            depth = int(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid depth: {item}") from exc
        if depth < 0:
            raise argparse.ArgumentTypeError("depth values must be >= 0")
        depths.append(depth)

    if not depths:
        raise argparse.ArgumentTypeError("at least one depth is required")
    return depths


def generate_rays(
    num_rays: int,
    seed: int = DEFAULT_SEED,
    bounds: AABB = DEFAULT_WORLD_BOUNDS,
    min_direction_component: float = 1e-12,
) -> list[Ray]:
    if num_rays <= 0:
        raise ValueError("num_rays must be > 0")

    bounds = square_bounds_from_aabb(bounds)
    side_length = bounds.max.x - bounds.min.x
    if side_length <= 0:
        raise ValueError("bounds must have positive area")

    rng = random.Random(seed)
    margin = side_length * 1e-9
    rays: list[Ray] = []

    while len(rays) < num_rays:
        origin = Vec2(
            x=rng.uniform(bounds.min.x + margin, bounds.max.x - margin),
            y=rng.uniform(bounds.min.y + margin, bounds.max.y - margin),
        )
        angle = rng.uniform(0.0, math.tau)
        direction = Vec2(math.cos(angle), math.sin(angle))

        # The experiment is about ordinary broad-phase traversal, not
        # axis-parallel edge cases, so generated rays avoid near-zero components.
        if (
            abs(direction.x) < min_direction_component
            or abs(direction.y) < min_direction_component
        ):
            continue

        rays.append(Ray(origin=origin, direction=direction))

    return rays


def _mix_checksum(checksum: int, value: int) -> int:
    return ((checksum ^ (value & CHECKSUM_MASK)) * CHECKSUM_PRIME) & CHECKSUM_MASK


def _grid_checksum(visited: list[VisitedCell]) -> int:
    checksum = CHECKSUM_OFFSET
    for cell in visited:
        checksum = _mix_checksum(checksum, cell.gridCoordinate.x + 1)
        checksum = _mix_checksum(checksum, cell.gridCoordinate.y + 1)
    return checksum


def _quadtree_checksum(
    visited,
    world_bounds: AABB,
    cells_per_axis: int,
) -> int:
    checksum = CHECKSUM_OFFSET
    cell_side_length = (world_bounds.max.x - world_bounds.min.x) / cells_per_axis

    for hit in visited:
        x = round((hit.partition.min.x - world_bounds.min.x) / cell_side_length)
        y = round((hit.partition.min.y - world_bounds.min.y) / cell_side_length)
        checksum = _mix_checksum(checksum, x + 1)
        checksum = _mix_checksum(checksum, y + 1)

    return checksum


def _write_algorithm_rows(
    raw_writer: csv.DictWriter,
    summary_writer: csv.DictWriter,
    algorithm: str,
    depth: int,
    cells_per_axis: int,
    rays: list[Ray],
    seed: int,
    shoot_ray,
    checksum_for_visited,
):
    total_runtime_ns = 0
    total_visited_partitions = 0
    min_visited_partitions: int | None = None
    max_visited_partitions = 0

    for ray_id, ray in enumerate(rays):
        started_at = perf_counter_ns()
        visited = shoot_ray(ray)
        runtime_ns = perf_counter_ns() - started_at
        checksum = checksum_for_visited(visited)
        visited_count = len(visited)

        total_runtime_ns += runtime_ns
        total_visited_partitions += visited_count
        min_visited_partitions = (
            visited_count
            if min_visited_partitions is None
            else min(min_visited_partitions, visited_count)
        )
        max_visited_partitions = max(max_visited_partitions, visited_count)

        raw_writer.writerow(
            {
                "algorithm": algorithm,
                "depth": depth,
                "cells_per_axis": cells_per_axis,
                "ray_id": ray_id,
                "origin_x": f"{ray.origin.x:.17g}",
                "origin_y": f"{ray.origin.y:.17g}",
                "direction_x": f"{ray.direction.x:.17g}",
                "direction_y": f"{ray.direction.y:.17g}",
                "visited_partition_count": visited_count,
                "runtime_ns": runtime_ns,
                "checksum": checksum,
            }
        )

    num_rays = len(rays)
    summary_writer.writerow(
        {
            "algorithm": algorithm,
            "depth": depth,
            "cells_per_axis": cells_per_axis,
            "num_rays": num_rays,
            "seed": seed,
            "total_runtime_ns": total_runtime_ns,
            "avg_runtime_ns_per_ray": total_runtime_ns / num_rays,
            "min_visited_partitions": min_visited_partitions,
            "max_visited_partitions": max_visited_partitions,
            "avg_visited_partitions": total_visited_partitions / num_rays,
            "total_visited_partitions": total_visited_partitions,
            "avg_runtime_ns_per_visited_partition": (
                total_runtime_ns / total_visited_partitions
                if total_visited_partitions
                else 0.0
            ),
        }
    )


def run_benchmark(
    num_rays: int = DEFAULT_NUM_RAYS,
    depths: list[int] | tuple[int, ...] = DEFAULT_DEPTHS,
    seed: int = DEFAULT_SEED,
    output_dir: str | Path = "data",
    world_bounds: AABB = DEFAULT_WORLD_BOUNDS,
) -> BenchmarkFiles:
    depths = list(depths)
    if not depths or any(depth < 0 for depth in depths):
        raise ValueError("depths must contain at least one value >= 0")

    world_bounds = square_bounds_from_aabb(world_bounds)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    raw_csv = output_path / "ray_benchmark_raw.csv"
    summary_csv = output_path / "ray_benchmark_summary.csv"
    rays = generate_rays(num_rays=num_rays, seed=seed, bounds=world_bounds)

    with raw_csv.open("w", newline="") as raw_file, summary_csv.open(
        "w", newline=""
    ) as summary_file:
        raw_writer = csv.DictWriter(raw_file, fieldnames=RAW_COLUMNS)
        summary_writer = csv.DictWriter(summary_file, fieldnames=SUMMARY_COLUMNS)
        raw_writer.writeheader()
        summary_writer.writeheader()

        for depth in depths:
            cells_per_axis = 2**depth
            grid = UniformGrid(layers=depth, world_bounds=world_bounds)
            quadtree = Quadtree(
                layers=depth,
                world_bounds=world_bounds,
                assign_objects=False,
            )

            _write_algorithm_rows(
                raw_writer=raw_writer,
                summary_writer=summary_writer,
                algorithm="uniform_grid",
                depth=depth,
                cells_per_axis=cells_per_axis,
                rays=rays,
                seed=seed,
                shoot_ray=grid.rayShoot,
                checksum_for_visited=_grid_checksum,
            )
            _write_algorithm_rows(
                raw_writer=raw_writer,
                summary_writer=summary_writer,
                algorithm="quadtree",
                depth=depth,
                cells_per_axis=cells_per_axis,
                rays=rays,
                seed=seed,
                shoot_ray=quadtree.shootRay,
                checksum_for_visited=lambda visited: _quadtree_checksum(
                    visited,
                    world_bounds,
                    cells_per_axis,
                ),
            )

    return BenchmarkFiles(raw_csv=raw_csv, summary_csv=summary_csv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark broad-phase ray traversal for a 2D uniform grid and quadtree."
    )
    parser.add_argument("--rays", type=int, default=DEFAULT_NUM_RAYS)
    parser.add_argument("--depths", type=parse_depths, default=list(DEFAULT_DEPTHS))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=Path("data"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    files = run_benchmark(
        num_rays=args.rays,
        depths=args.depths,
        seed=args.seed,
        output_dir=args.out,
    )

    print(f"Wrote raw CSV: {files.raw_csv}")
    print(f"Wrote summary CSV: {files.summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
