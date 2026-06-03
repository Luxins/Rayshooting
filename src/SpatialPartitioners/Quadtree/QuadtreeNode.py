from BasicGeometry.BasicGeometry import AABB, Vec2
from textwrap import indent

class QuadtreeNode:
    myIndex: int = -1
    children: list[int, int, int, int]
    # List of objects contained in the quadtree node:
    objects: list[AABB]

    def __init__(self, index: int, bounds: AABB, center: Vec2, objects: list[AABB] = [], children: list[int, int, int, int] = []):
        self.myIndex = index
        self.bounds: AABB = bounds
        self.center: Vec2 = center
        self.children = children
        self.objects = objects
    
    def setChildren(self, children: list[int, int, int, int]):
        self.children = children
    
    def setObjects(self, objects: list[AABB]):
        self.objects = objects
    
    def takeOwnership(self, obj: AABB):
        self.objects.append(obj)

    def fullyContains(self, object: AABB):
        return (self.bounds.min.x <= object.min.x and
                self.bounds.min.y <= object.min.y and
                self.bounds.max.x >= object.max.x and
                self.bounds.max.y >= object.max.y)
    
    def __str__(self)-> str:
        objects_str: str = "\n\n".join(str(obj) for obj in self.objects[0:min(3, len(self.objects))])
        return f"Node bounds:\n{indent(self.bounds.__str__(), '\t')}\n\nObjects enclosed (sample):\n{indent(objects_str, '\t')}"