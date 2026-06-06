from Ray.Ray import Ray, RayHit, RayInterval
from BasicGeometry.BasicGeometry import AABB, Vec2
from dataclasses import dataclass
import math

@dataclass
class GridCoordinate:
    x: int = 0
    y: int = 0

    def __str__(self):
        return f"Grid coordinate x: {self.x} y: {self.y}"

@dataclass
class AxisTraversal:
    step: int
    t_next_wall: float
    t_wall_to_wall: float

def initAxisTraversal(
    originCoord: float,
    directionCoord: float,
    gridMinCoord: float,
    cellIndex: int,
    cellSideLength: float
) -> AxisTraversal:
    step = 1 if directionCoord > 0 else -1

    nextWallIndex = cellIndex + 1 if step > 0 else cellIndex

    nextWallCoord = gridMinCoord + nextWallIndex * cellSideLength

    distanceToNextWall = abs(nextWallCoord - originCoord)

    t_next_wall = distanceToNextWall / abs(directionCoord)

    t_wall_to_wall = cellSideLength / abs(directionCoord)

    return AxisTraversal(
        step=step,
        t_next_wall=t_next_wall,
        t_wall_to_wall=t_wall_to_wall
    )


# TODO: Leaking GridCoordinate to external callers is a bad idea, as they have no way of interpreting it.
# However, we do not need to store realistic partitions either for the scope of the essay...
@dataclass
class VistitedCell:
    gridCoordinate: GridCoordinate
    rayInterval: RayInterval

class UniformGrid:
    def __init__(self, layers: int, objectCloud: list[AABB]):
        """Using the term layers as a parameter even though the uniform grid is flat. Will match a Quadtree in terms of partition for the same layer argument."""
        worldBound: AABB = AABB.mergeMany(objectCloud)
        worldExtendX: float = worldBound.max.x - worldBound.min.x
        worldExtendY: float = worldBound.max.y - worldBound.min.y

        worldSideLength: float = max(worldExtendX, worldExtendY)
        self.partitionSideLength: float = worldSideLength / (2**layers)
        self.numPartitionsPerAxis: int = 2**layers

        self.gridUpperLeft: Vec2 = Vec2(
            x=worldBound.min.x,
            y=worldBound.min.y
        )
    
    def worldToGrid(self, p: Vec2)-> GridCoordinate:
        """This function is crucial for determining what grid cell the origin is in!"""
        relativeX: float = p.x - self.gridUpperLeft.x
        relativeY: float = p.y - self.gridUpperLeft.y

        return GridCoordinate(
            x= math.floor(relativeX / self.partitionSideLength),
            y=math.floor(relativeY / self.partitionSideLength)
        )

    # def rayShoot(self, ray: Ray)-> list[VistitedCell]:
    #     visitedCells: list[VistitedCell] = []
    #     # Als erstes möchten wir für den Origin berechnen welche Zellwand mit einem kleineren t erreicht werden kann.
    #     # Zur vereinfachung nehmen wir erstmal an, dass ray.direction.x/y != 0 (Edge case handling wird später hinzugefügt)

    #     cellOfOrigin: GridCoordinate = self.worldToGrid(ray.origin)
        
    #     # Messen wir nun die Zeit bis zur nächsten Vertikalen Zellwand.
    #     # Erstmal müssen wir entscheiden, ob wir gegen die linke oder rechte Zellwand laufen.
    #     hittingRightWall: bool = True if ray.direction.x > 0 else False

    #     # Jetzt messen wir die Distanz zwischen der Zellwand und dem Origin:
    #     distanceToNextVerticalWall: float = None
    #     # Machen wir dafür erstmal ray.origin relativ zu Grid.upperLeft
    #     relativeOrigin: Vec2 = ray.origin - self.gridUpperLeft
    #     if hittingRightWall:
    #         # Wir können die X-Koordinate der rechten Wall relativ zu grid.upperLeft berechnen:
    #         nextRightWall: float = (cellOfOrigin.x + 1) * self.partitionSideLength
    #         # Nun der Abstand zwischen Origin und der Wall:
    #         distanceToNextVerticalWall = nextRightWall - relativeOrigin.x
    #     elif not hittingRightWall:
    #         nextLeftWall: float = cellOfOrigin.x * self.partitionSideLength
    #         distanceToNextVerticalWall = abs(nextLeftWall - relativeOrigin.x)
        
    #     # Wir wiederholen den gleichen Prozess für distanceToNextHorizontalWall
    #     hittingLowerWall: bool = True if ray.direction.y > 0 else False

    #     distanceToNextHorizontalWall: float = None
    #     # relativeOrigin kann von oben wiederverwandt werden
    #     if hittingLowerWall:
    #         nextLowerWall: float = (cellOfOrigin.y + 1) * self.partitionSideLength
    #         distanceToNextHorizontalWall = nextLowerWall - relativeOrigin.y
    #     elif not hittingLowerWall:
    #         nextUpperWall: float = cellOfOrigin.y * self.partitionSideLength
    #         distanceToNextHorizontalWall = abs(nextUpperWall - relativeOrigin.y)
        
    #     # Wir wissen nun garantiert, dass die Zelle nach folgenden t-Wert verlassen wird:
    #     tTillNextWall: float = min(distanceToNextVerticalWall, distanceToNextHorizontalWall)
    #     # Wir können also nun die Zelle als visited speichern, in der sich der Origin befindet
    #     visitedCells.append(
    #         VistitedCell(
    #             gridCoordinate=cellOfOrigin,
    #             rayInterval=RayInterval(
    #                 t_enter=0.001,
    #                 t_exit=tTillNextWall
    #             )
    #         )
    #     )
        
    #     # Nun können wir uns etwas bauen, um weitere Iterationen zu vereinfachen:
    #     # Der Abstand von einer Vertikalen/Horizontalen Zellwand zur nächsten ist immer Konstant.
    #     # Dementsprechend ist auch die Zeit Konstant, die die Ray benötigt, um von einer Zellwand zur nächsten zur kommen.
    #     # Lass uns diese Zeit berechenen:
    #     tVerticalToVertical: float = abs(self.partitionSideLength / ray.direction.x)
    #     tHorizontalToHorizontal: float = abs(self.partitionSideLength / ray.direction.y)

    #     # Für die Iteration bereiten wir zuerst die Zellkoordinate, der nächsten Zelle vor
    #     nextCell: GridCoordinate = cellOfOrigin
    #     if (distanceToNextVerticalWall < distanceToNextHorizontalWall):
    #         # Dann hat sich der x-Zellenindex geändert.
    #         nextCell.x += 1 if hittingRightWall else -1
    #     elif distanceToNextHorizontalWall < distanceToNextVerticalWall:
    #         # Dann hat isch der y-Zellenindex geändert.
    #         nextCell.y += 1 if hittingLowerWall else -1
        
    #     # Jetzt iterieren wir so lange, bis die Zellenindex in nextCell nicht mehr valide ist.
    #     while (nextCell.x >= 0 and
    #            nextCell.y >= 0 and
    #            nextCell.x < self.numPartitionsPerAxis and
    #            nextCell.y < self.numPartitionsPerAxis):
            

                
    def rayShoot(self, ray: Ray) -> list[VistitedCell]:
        visitedCells: list[VistitedCell] = []

        currentCell: GridCoordinate = self.worldToGrid(ray.origin)

        xTraversal = initAxisTraversal(
            originCoord=ray.origin.x,
            directionCoord=ray.direction.x,
            gridMinCoord=self.gridUpperLeft.x,
            cellIndex=currentCell.x,
            cellSideLength=self.partitionSideLength
        )

        yTraversal = initAxisTraversal(
            originCoord=ray.origin.y,
            directionCoord=ray.direction.y,
            gridMinCoord=self.gridUpperLeft.y,
            cellIndex=currentCell.y,
            cellSideLength=self.partitionSideLength
        )

        tEnterCurrentCell: float = 0.0

        while (
            currentCell.x >= 0 and
            currentCell.y >= 0 and
            currentCell.x < self.numPartitionsPerAxis and
            currentCell.y < self.numPartitionsPerAxis
        ):
            tExitCurrentCell = min(
                xTraversal.t_next_wall,
                yTraversal.t_next_wall
            )

            visitedCells.append(
                VistitedCell(
                    gridCoordinate=GridCoordinate(
                        currentCell.x,
                        currentCell.y
                    ),
                    rayInterval=RayInterval(
                        t_enter=tEnterCurrentCell,
                        t_exit=tExitCurrentCell
                    )
                )
            )

            if xTraversal.t_next_wall < yTraversal.t_next_wall:
                currentCell.x += xTraversal.step
                tEnterCurrentCell = xTraversal.t_next_wall
                xTraversal.t_next_wall += xTraversal.t_wall_to_wall

            else:
                currentCell.y += yTraversal.step
                tEnterCurrentCell = yTraversal.t_next_wall
                yTraversal.t_next_wall += yTraversal.t_wall_to_wall

        return visitedCells
