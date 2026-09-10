# Rayshooting

Small experimental Python project for comparing two broad-phase ray traversal
strategies in a two-dimensional unit square:

- a uniform grid with incremental cell traversal
- a complete quadtree with the same final leaf resolution

The intent is not to build a production renderer. The project isolates the
traversal step so the two structures can be compared under equal input
conditions: the same generated rays, the same square bounds, and the same leaf
resolution at each tested depth.

## Getting Started

Clone the repository and enter the project folder:

```sh
git clone https://github.com/Luxins/Rayshooting.git
cd Rayshooting
```

Create and activate a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```sh
pip install -r requirements.txt
pip install -e .
```

Run the tests:

```sh
python -m unittest
```

Run the benchmark with the default settings:

```sh
python main.py
```

This writes the raw and summarized benchmark CSV files to `data/`. You can also
choose the number of rays, tested depths, seed, and output directory:

```sh
python main.py --rays 10000 --depths 2,3,4,5,6,7,8 --seed 42 --out data
```

## Project Structure

- `main.py` starts the benchmark command line interface.
- `src/BasicGeometry/` contains the vector and axis-aligned bounding-box helpers.
- `src/Ray/` contains the ray representation.
- `src/SpatialPartitioners/UniformGrid/` contains the uniform-grid traversal.
- `src/SpatialPartitioners/Quadtree/` contains the complete quadtree traversal.
- `src/Benchmark/` generates rays, runs both algorithms, and writes CSV output.
- `tests/` contains traversal and benchmark regression tests.
- `data/` contains the current benchmark CSV outputs.
- `analysis_results/` contains the recorded analysis tables and figures for the
  experiment write-up.

## Current Experiment

The recorded run uses 10,000 rays, depths 2 through 8, and seed 42. In that
setup, the grid and complete quadtree agree on the visited leaf partitions for
the generated rays, but the grid traversal is consistently faster. The result is
specific to an equal-resolution complete quadtree; adaptive quadtrees may behave
differently when they can keep empty or simple regions coarse.
