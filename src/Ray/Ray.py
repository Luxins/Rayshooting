from BasicGeometry.BasicGeometry import Vec2, AABB
from dataclasses import dataclass, field


class Ray:
    def __init__(self, origin=Vec2, direction=Vec2, min_t: float = 0, max_t: float = float('inf')):
        self.origin: Vec2 = origin
        self.direction: Vec2 = direction

        min_t: float = min_t
        # max_t < float('inf') zu machen, bedeutet man hat ein RaySegment anstatt eine komplette Ray!
        max_t: float = max_t

    def PointAt(self, t: float)-> Vec2:
        return self.origin + self.direction * t


class RayHit:
    """Provides a shared contract. Space Partitioners return a list of RayHits when queried for ray-shooting.
    A RayHit indicates the Partition (AABB) that was hit, as well as the point of time at which the ray first intersects with that partition intersection_t"""
    partition: AABB
    intersection_t: float


