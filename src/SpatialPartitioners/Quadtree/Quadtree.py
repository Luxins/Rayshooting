from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from textwrap import indent
from typing import TYPE_CHECKING

from BasicGeometry.BasicGeometry import (
    AABB,
    Vec2,
    square_bounds_for_aabbs,
    square_bounds_from_aabb,
)
from Ray.Ray import Ray, RayHit, RayInterval, intersect
from SpatialPartitioners.Quadtree.QuadtreeNode import QuadtreeNode, TraversalItem

if TYPE_CHECKING:
    from AABBDistribution.AABBDistribution import AABBDistribution


class Quadtree:
    def __init__(
        self,
        scene: AABBDistribution | Sequence[AABB] | None = None,
        layers: int = 1,
        world_bounds: AABB | None = None,
        assign_objects: bool = True,
    ):
        """Create a complete quadtree whose leaves are at depth ``layers``."""
        if layers < 0:
            raise ValueError("layers must be >= 0")

        samples = self._extractSamples(scene)
        if world_bounds is None:
            if not samples:
                raise ValueError("scene or world_bounds is required")
            world_bounds = square_bounds_for_aabbs(samples)
        else:
            world_bounds = square_bounds_from_aabb(world_bounds)

        self.layers: int = layers
        self.maxDepth: int = layers
        self.scene = scene
        self.worldBounds: AABB = world_bounds
        self.nodes: list[QuadtreeNode] = []

        self.buildRecursive(self.worldBounds, currentDepth=0)

        self.objects: list[AABB] = samples
        if assign_objects and self.objects:
            self.assignObjectsToCells(self.objects, cellIndex=0)

    @staticmethod
    def _extractSamples(scene: AABBDistribution | Sequence[AABB] | None) -> list[AABB]:
        if scene is None:
            return []
        if hasattr(scene, "samples"):
            return list(scene.samples)
        return list(scene)

    @staticmethod
    def _splitBounds(bounds: AABB) -> list[AABB]:
        center = bounds.center

        return [
            AABB(
                min=Vec2(bounds.min.x, bounds.min.y),
                max=Vec2(center.x, center.y),
            ),
            AABB(
                min=Vec2(center.x, bounds.min.y),
                max=Vec2(bounds.max.x, center.y),
            ),
            AABB(
                min=Vec2(center.x, center.y),
                max=Vec2(bounds.max.x, bounds.max.y),
            ),
            AABB(
                min=Vec2(bounds.min.x, center.y),
                max=Vec2(center.x, bounds.max.y),
            ),
        ]

    def assignObjectsToCells(self, objects: list[AABB], cellIndex: int):
        for obj in objects:
            self.assignObjectToCell(obj, cellIndex)

    def assignObjectToCell(self, obj: AABB, cellIndex: int):
        currentCell: QuadtreeNode = self.nodes[cellIndex]

        for childIndex in currentCell.children:
            child = self.nodes[childIndex]
            if child.fullyContains(obj):
                return self.assignObjectToCell(obj, child.myIndex)

        # If no child fully contains the object, the current node owns it.
        currentCell.takeOwnership(obj)

    def buildRecursive(self, bounds: AABB, currentDepth: int) -> int:
        node: QuadtreeNode = QuadtreeNode(len(self.nodes), bounds, bounds.center)
        self.nodes.append(node)

        if currentDepth < self.maxDepth:
            childIndices = [
                self.buildRecursive(childBounds, currentDepth + 1)
                for childBounds in self._splitBounds(bounds)
            ]
            node.setChildren(childIndices)

        return node.myIndex

    def __str__(self):
        metadata: str = (
            f"Number of Nodes:\t{len(self.nodes)}\n"
            f"Root Node bounds:\n{indent(self.nodes[0].bounds.__str__(), '\t')}"
        )
        node_data: str = "\n\n".join(str(node) for node in self.nodes)
        return f"{metadata}\n\n{node_data}"

    def shootRay(self, ray: Ray) -> list[RayHit]:
        """Return leaf partitions intersected by the ray, sorted by entry time."""
        root: QuadtreeNode = self.nodes[0]
        rayInterval = RayInterval(
            getattr(ray, "min_t", 0.0),
            getattr(ray, "max_t", float("inf")),
        )
        rootIntersected, rootIntersectedInterval = intersect(
            root.bounds,
            ray,
            rayInterval,
        )

        if not rootIntersected:
            return []

        results: list[RayHit] = []
        queue: deque[TraversalItem] = deque(
            [TraversalItem(node=root, interval=rootIntersectedInterval)]
        )

        while queue:
            traversalItem: TraversalItem = queue.popleft()
            node = traversalItem.node

            if node.isLeaf():
                results.append(
                    RayHit(
                        partition=node.bounds,
                        t_enter=traversalItem.interval.t_enter,
                        t_exit=traversalItem.interval.t_exit,
                    )
                )
                continue

            # Only descend into children whose square bounds overlap the ray.
            for childIndex in node.children:
                child = self.nodes[childIndex]
                childIntersected, childInterval = intersect(
                    child.bounds,
                    ray=ray,
                    rayInterval=traversalItem.interval,
                )
                if childIntersected:
                    queue.append(TraversalItem(child, childInterval))

        results.sort(key=lambda hit: hit.t_enter)
        return results

    def listNodesWithOrigin(self, ray: Ray) -> list[QuadtreeNode]:
        containsOrigin: list[QuadtreeNode] = []
        stack: list[QuadtreeNode] = [self.nodes[0]]

        while stack:
            nodeWithOrigin: QuadtreeNode = stack.pop()
            containsOrigin.append(nodeWithOrigin)
            for childIndex in nodeWithOrigin.children:
                child = self.nodes[childIndex]
                if child.bounds.containsPoint(ray.origin):
                    stack.append(child)

        return containsOrigin


if __name__ == "__main__":
    from AABBDistribution.AABBDistribution import AABBDistribution
    from py_game.Loop import loopSingleton

    scene: AABBDistribution = AABBDistribution(20)
    loopSingleton.centerSimulationInWinow(scene)

    tree: Quadtree = Quadtree(scene, 3)
    root = tree.nodes[0]
    ray: Ray = Ray(
        origin=Vec2(
            x=root.bounds.min.x + 30,
            y=root.bounds.min.y + 30,
        ),
        direction=Vec2(1, 1),
    )

    for hit in tree.shootRay(ray):
        hit.partition.shade = True

    loopSingleton.addRay(ray)
    loopSingleton.run()
