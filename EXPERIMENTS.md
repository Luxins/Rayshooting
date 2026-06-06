# Broad-Phase Ray Traversal Benchmark

This benchmark measures only the broad-phase traversal cost of determining which spatial partitions are visited by a ray. It does not measure object-level ray intersections or collision detection narrow phase.

## What Is Compared

The benchmark compares two 2D spatial partitioners:

- `uniform_grid`
- `quadtree`

Both algorithms receive the same world bounds and the same generated rays. They return only the leaf partitions visited by each ray.

The experiment uses Modus A: same partition depth. For depth `d`, the uniform grid has `2^d` cells per axis and `4^d` total cells. The quadtree has max depth `d`, so a complete quadtree also has `4^d` leaf partitions.

## What Is Not Measured

The benchmark does not include:

- object collision detection
- ray-object intersections
- rendering
- physics
- adaptive quadtree behavior
- multiprocessing or GPU acceleration

The goal is understandable, reproducible raw data for comparing traversal cost.

## Rays And Bounds

The default world bounds are the unit square from `(0, 0)` to `(1, 1)`.

Rays are generated once per benchmark run and reused for both partitioners at every depth. Origins are sampled uniformly inside the square bounds. Directions are generated from random angles. The generator rejects directions whose x or y component is too close to zero, because the paper experiment is not focused on axis-parallel edge cases.

The default seed is `42`.

## CSV Output

The benchmark writes CSV files to the selected output directory, `data/` by default.

`ray_benchmark_raw.csv` contains one row per algorithm, depth, and ray:

- `algorithm`
- `depth`
- `cells_per_axis`
- `ray_id`
- `origin_x`
- `origin_y`
- `direction_x`
- `direction_y`
- `visited_partition_count`
- `runtime_ns`
- `checksum`

`ray_benchmark_summary.csv` contains one row per algorithm and depth:

- `algorithm`
- `depth`
- `cells_per_axis`
- `num_rays`
- `seed`
- `total_runtime_ns`
- `avg_runtime_ns_per_ray`
- `min_visited_partitions`
- `max_visited_partitions`
- `avg_visited_partitions`
- `total_visited_partitions`
- `avg_runtime_ns_per_visited_partition`

The checksum is derived from visited partition coordinates. It is included as a simple guard that the visited partitions were actually consumed by the benchmark.

## Run The Benchmark

Default run:

```bash
.venv/bin/python main.py
```

Configured run:

```bash
.venv/bin/python main.py --rays 100000 --depths 2,3,4,5,6,7,8 --seed 42 --out data
```

Small smoke run:

```bash
.venv/bin/python main.py --rays 100 --depths 2,3 --seed 42 --out data
```

## Run Tests

```bash
.venv/bin/python -m unittest discover -s tests
```

## Assumptions And Limitations

Generated benchmark rays avoid origins exactly on bounds and directions with near-zero components. The traversal code handles simple boundary cases well enough to terminate, but perfect production-grade tie handling is outside the scope of this measurement.

The quadtree used here is complete, not adaptive. That is intentional for the same-depth comparison.
