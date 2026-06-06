import csv
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from BasicGeometry.BasicGeometry import AABB, Vec2
from Benchmark.RayBenchmark import generate_rays, main as benchmark_main
from Ray.Ray import Ray
from SpatialPartitioners.Quadtree.Quadtree import Quadtree
from SpatialPartitioners.UniformGrid.UniformGrid import UniformGrid


BOUNDS = AABB(Vec2(0.0, 0.0), Vec2(1.0, 1.0))


def quadtree_leaf_coordinate(hit, cells_per_axis: int) -> tuple[int, int]:
    cell_side_length = 1.0 / cells_per_axis
    return (
        round(hit.partition.min.x / cell_side_length),
        round(hit.partition.min.y / cell_side_length),
    )


class RayTraversalTests(unittest.TestCase):
    def test_uniform_grid_returns_non_empty_for_normal_ray(self):
        grid = UniformGrid(layers=3, world_bounds=BOUNDS)
        ray = Ray(origin=Vec2(0.25, 0.25), direction=Vec2(0.8, 0.35))

        visited = grid.rayShoot(ray)

        self.assertGreater(len(visited), 0)
        for cell in visited:
            self.assertTrue(grid.containsCell(cell.gridCoordinate))

    def test_quadtree_returns_non_empty_for_normal_ray(self):
        quadtree = Quadtree(layers=3, world_bounds=BOUNDS, assign_objects=False)
        ray = Ray(origin=Vec2(0.25, 0.25), direction=Vec2(0.8, 0.35))

        visited = quadtree.shootRay(ray)

        self.assertGreater(len(visited), 0)
        for hit in visited:
            self.assertGreaterEqual(hit.partition.min.x, BOUNDS.min.x)
            self.assertGreaterEqual(hit.partition.min.y, BOUNDS.min.y)
            self.assertLessEqual(hit.partition.max.x, BOUNDS.max.x)
            self.assertLessEqual(hit.partition.max.y, BOUNDS.max.y)

    def test_both_algorithms_terminate_for_many_random_rays(self):
        rays = generate_rays(num_rays=300, seed=42, bounds=BOUNDS)

        for depth in (1, 2, 3, 4, 5):
            cells_per_axis = 2**depth
            reasonable_upper_bound = 4 * cells_per_axis + 4
            grid = UniformGrid(layers=depth, world_bounds=BOUNDS)
            quadtree = Quadtree(
                layers=depth,
                world_bounds=BOUNDS,
                assign_objects=False,
            )

            for ray in rays:
                grid_visited = grid.rayShoot(ray)
                quadtree_visited = quadtree.shootRay(ray)

                self.assertGreater(len(grid_visited), 0)
                self.assertGreater(len(quadtree_visited), 0)
                self.assertLessEqual(len(grid_visited), reasonable_upper_bound)
                self.assertLessEqual(len(quadtree_visited), reasonable_upper_bound)

    def test_grid_and_complete_quadtree_agree_for_simple_non_boundary_ray(self):
        ray = Ray(origin=Vec2(0.123, 0.234), direction=Vec2(0.731, 0.317))

        for depth in (0, 1, 2, 3, 4, 5):
            cells_per_axis = 2**depth
            grid = UniformGrid(layers=depth, world_bounds=BOUNDS)
            quadtree = Quadtree(
                layers=depth,
                world_bounds=BOUNDS,
                assign_objects=False,
            )

            grid_coordinates = [
                (cell.gridCoordinate.x, cell.gridCoordinate.y)
                for cell in grid.rayShoot(ray)
            ]
            quadtree_coordinates = [
                quadtree_leaf_coordinate(hit, cells_per_axis)
                for hit in quadtree.shootRay(ray)
            ]

            self.assertEqual(grid_coordinates, quadtree_coordinates)


class BenchmarkMainTests(unittest.TestCase):
    def test_benchmark_main_writes_raw_and_summary_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            exit_code = benchmark_main(
                [
                    "--rays",
                    "100",
                    "--depths",
                    "2,3",
                    "--seed",
                    "42",
                    "--out",
                    tmp_dir,
                ]
            )

            self.assertEqual(exit_code, 0)
            raw_csv = Path(tmp_dir) / "ray_benchmark_raw.csv"
            summary_csv = Path(tmp_dir) / "ray_benchmark_summary.csv"
            self.assertTrue(raw_csv.exists())
            self.assertTrue(summary_csv.exists())

            with raw_csv.open() as raw_file:
                raw_rows = list(csv.DictReader(raw_file))
            with summary_csv.open() as summary_file:
                summary_rows = list(csv.DictReader(summary_file))

            self.assertEqual(len(raw_rows), 2 * 2 * 100)
            self.assertEqual(len(summary_rows), 2 * 2)
            self.assertEqual(
                {row["algorithm"] for row in summary_rows},
                {"uniform_grid", "quadtree"},
            )


if __name__ == "__main__":
    unittest.main()
