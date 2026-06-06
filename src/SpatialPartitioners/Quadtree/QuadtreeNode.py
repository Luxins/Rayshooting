from dataclasses import dataclass
from textwrap import indent

from BasicGeometry.BasicGeometry import AABB, Vec2
from Ray.Ray import RayInterval


class QuadtreeNode:
    myIndex: int = -1
    children: list[int]
    objects: list[AABB]

    def __init__(
        self,
        index: int,
        bounds: AABB,
        center: Vec2,
        objects: list[AABB] | None = None,
        children: list[int] | None = None,
    ):
        self.myIndex = index
        self.bounds: AABB = bounds
        self.center: Vec2 = center
        self.children = [] if children is None else children
        self.objects = [] if objects is None else objects

    def isLeaf(self) -> bool:
        return len(self.children) == 0

    def setChildren(self, children: list[int]):
        self.children = children

    def setObjects(self, objects: list[AABB]):
        self.objects = objects

    def takeOwnership(self, obj: AABB):
        self.objects.append(obj)

    def fullyContains(self, obj: AABB):
        return (
            self.bounds.min.x <= obj.min.x
            and self.bounds.min.y <= obj.min.y
            and self.bounds.max.x >= obj.max.x
            and self.bounds.max.y >= obj.max.y
        )

    def __str__(self) -> str:
        objects_str: str = "\n\n".join(
            str(obj) for obj in self.objects[0 : min(3, len(self.objects))]
        )
        return (
            f"Node bounds:\n{indent(self.bounds.__str__(), '\t')}\n\n"
            f"Objects enclosed (sample):\n{indent(objects_str, '\t')}"
        )


@dataclass
class TraversalItem:
    node: QuadtreeNode
    interval: RayInterval
