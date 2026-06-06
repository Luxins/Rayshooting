from dataclasses import dataclass
import math

from BasicGeometry.BasicGeometry import (
    AABB,
    Vec2,
    square_bounds_for_aabbs,
    square_bounds_from_aabb,
)
from Ray.Ray import Ray, RayInterval


@dataclass(frozen=True)
class GridCoordinate:
    x: int = 0
    y: int = 0

    def __str__(self):
        return f"Grid coordinate x: {self.x} y: {self.y}"


@dataclass
class AxisTraversal:
    step: int
    timeToNextWall: float
    timeBetweenWalls: float


def initAxisTraversal(
    originCoord: float,
    directionCoord: float,
    gridMinCoord: float,
    cellIndex: int,
    cellSideLength: float,
) -> AxisTraversal:
    if directionCoord == 0:
        return AxisTraversal(
            step=0,
            timeToNextWall=float("inf"),
            timeBetweenWalls=float("inf"),
        )

    step = 1 if directionCoord > 0 else -1
    nextWallIndex = cellIndex + 1 if step > 0 else cellIndex
    nextWallCoord = gridMinCoord + nextWallIndex * cellSideLength

    return AxisTraversal(
        step=step,
        timeToNextWall=abs(nextWallCoord - originCoord) / abs(directionCoord),
        timeBetweenWalls=cellSideLength / abs(directionCoord),
    )


@dataclass
class VisitedCell:
    gridCoordinate: GridCoordinate
    rayInterval: RayInterval


# Backwards-compatible alias for existing notebooks/scripts that may import the typo.
VistitedCell = VisitedCell


class UniformGrid:
    def __init__(
        self,
        layers: int,
        objectCloud: list[AABB] | None = None,
        world_bounds: AABB | None = None,
    ):
        """Create a 2D grid with 2^layers cells per axis."""
        if layers < 0:
            raise ValueError("layers must be >= 0")

        if world_bounds is None:
            if not objectCloud:
                raise ValueError("objectCloud or world_bounds is required")
            world_bounds = square_bounds_for_aabbs(objectCloud)
        else:
            world_bounds = square_bounds_from_aabb(world_bounds)

        self.layers: int = layers
        self.worldBounds: AABB = world_bounds
        self.numPartitionsPerAxis: int = 2**layers
        self.cells_per_axis: int = self.numPartitionsPerAxis
        self.partitionSideLength: float = (
            self.worldBounds.max.x - self.worldBounds.min.x
        ) / self.numPartitionsPerAxis
        self.gridUpperLeft: Vec2 = self.worldBounds.min

    def worldToGrid(self, p: Vec2) -> GridCoordinate:
        """Map a point inside the grid bounds to its cell coordinate."""
        relativeX: float = p.x - self.gridUpperLeft.x
        relativeY: float = p.y - self.gridUpperLeft.y

        # Clamp so points exactly on the square's max boundary still map to
        # the final cell instead of one-past-the-grid.
        x = min(
            max(math.floor(relativeX / self.partitionSideLength), 0),
            self.numPartitionsPerAxis - 1,
        )
        y = min(
            max(math.floor(relativeY / self.partitionSideLength), 0),
            self.numPartitionsPerAxis - 1,
        )

        return GridCoordinate(x=x, y=y)

    def containsCell(self, cell: GridCoordinate) -> bool:
        return (
            0 <= cell.x < self.numPartitionsPerAxis
            and 0 <= cell.y < self.numPartitionsPerAxis
        )

    def rayShoot(self, ray: Ray) -> list[VisitedCell]:
        if not self.worldBounds.containsPoint(ray.origin):
            return []

        currentCell: GridCoordinate = self.worldToGrid(ray.origin)

        xTraversal = initAxisTraversal(
            originCoord=ray.origin.x,
            directionCoord=ray.direction.x,
            gridMinCoord=self.gridUpperLeft.x,
            cellIndex=currentCell.x,
            cellSideLength=self.partitionSideLength,
        )
        yTraversal = initAxisTraversal(
            originCoord=ray.origin.y,
            directionCoord=ray.direction.y,
            gridMinCoord=self.gridUpperLeft.y,
            cellIndex=currentCell.y,
            cellSideLength=self.partitionSideLength,
        )

        stepX: int = xTraversal.step
        stepY: int = yTraversal.step
        timeToNextVerticalWall: float = xTraversal.timeToNextWall
        timeToNextHorizontalWall: float = yTraversal.timeToNextWall
        timeBetweenVerticalWalls: float = xTraversal.timeBetweenWalls
        timeBetweenHorizontalWalls: float = yTraversal.timeBetweenWalls

        enteredCurrentCellAt: float = getattr(ray, "min_t", 0.0)
        visitedCells: list[VisitedCell] = []

        while self.containsCell(currentCell):
            leavesCurrentCellAt = min(
                timeToNextVerticalWall,
                timeToNextHorizontalWall,
                getattr(ray, "max_t", float("inf")),
            )

            visitedCells.append(
                VisitedCell(
                    gridCoordinate=GridCoordinate(currentCell.x, currentCell.y),
                    rayInterval=RayInterval(
                        t_enter=enteredCurrentCellAt,
                        t_exit=leavesCurrentCellAt,
                    ),
                )
            )

            if leavesCurrentCellAt >= getattr(ray, "max_t", float("inf")):
                break

            # Move through the first wall hit by the ray. If a corner is hit
            # exactly, advance both axes to avoid zero-length loops.
            crossesVerticalWall = (
                timeToNextVerticalWall <= timeToNextHorizontalWall
            )
            crossesHorizontalWall = (
                timeToNextHorizontalWall <= timeToNextVerticalWall
            )

            if not crossesVerticalWall and not crossesHorizontalWall:
                break

            if crossesVerticalWall:
                currentCell = GridCoordinate(currentCell.x + stepX, currentCell.y)
                timeToNextVerticalWall += timeBetweenVerticalWalls

            if crossesHorizontalWall:
                currentCell = GridCoordinate(currentCell.x, currentCell.y + stepY)
                timeToNextHorizontalWall += timeBetweenHorizontalWalls

            enteredCurrentCellAt = leavesCurrentCellAt

        return visitedCells
