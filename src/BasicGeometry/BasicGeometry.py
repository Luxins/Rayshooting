from dataclasses import dataclass
from statistics import mean
from math import sqrt
from typing import Optional

@dataclass
class VecInt2:
    """This trash is required because pygame internally works with ints"""
    x: int = 0
    y: int = 0
@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    @property
    def len(self)->float:
        return sqrt(self.x**2 + self.y**2)

    def normalize(self)-> "Vec2":
        return Vec2(
            x=self.x / self.len,
            y=self.y / self.len
        )

    def __sub__(self, other: "Vec2")-> "Vec2":
        return Vec2(
            self.x - other.x,
            self.y - other.y
        )
    
    def __add__(self, other: "Vec2")-> "Vec2":
        return Vec2(
            self.x + other.x,
            self.y + other.y
        ) 

    def __mul__(self, other: float)-> "Vec2":
        return Vec2(
            self.x * other,
            self.y * other
        )

    @staticmethod    
    def squaredDistance(a: "Vec2", b: "Vec2")-> float:
        dx: float = a.x - b.x
        dy: float = a.y - b.y
        return dx * dx + dy * dy



@dataclass
class AABB:
    min: Vec2
    max: Vec2
    
    # Further attributes for rendering:
    skip: bool = False # Skips the object placement step in the flipbook
    shade: bool = False # Draws the given object with an opaque fill

    def containsPoint(self, point: Vec2)-> bool:
        return (
            self.min.x <= point.x and
            self.max.x >= point.x and
            self.min.y <= point.y and
            self.max.y >= point.y
        )

    @property
    def center(self)-> Vec2:
        return Vec2(
            mean((self.min.x, self.max.x)),
            mean((self.min.y, self.max.y))
            )

    def collidesWith(self, other: "AABB")-> bool:
        return (
            self.min.x <= other.max.x and
            self.max.x >= other.min.x and
            self.min.y <= other.max.y and
            self.max.y >= other.min.y
        )

    def longestAxis(self)-> int:
        """1 means x-axis 2 means y-axis"""
        if (self.max.x - self.min.x > self.max.y - self.min.y):
            return 1
        else:
            return 2
    

    def volume(self)-> float:
        dx: float = self.max.x - self.min.x
        dy: float = self.max.y - self.min.y

        return dx * dy

    @staticmethod
    def merge(a: "AABB", b: "AABB"):
        res: "AABB" = AABB(
            min = Vec2(
                x = min(a.min.x, b.min.x),
                y = min(a.min.y, b.min.y)
            ),
            max = Vec2(
                x = max(a.max.x, b.max.x),
                y = max(a.max.y, b.max.y)
            )
        )
        return res
    
    @staticmethod
    def mergeMany(l: list["AABB"])-> "AABB":
        assert len(l) >= 1
        
        if len(l) == 1:
            return l[0]
        
        cur: AABB = l[0]
        for elem in l[1:]:
            cur = AABB.merge(cur, elem)
        
        return cur
    
    def __str__(self)-> str:
        return f"min: [x={self.min.x:.1f} y={self.min.y:.1f}]\nmax: [x={self.max.x:.1f} y={self.max.y:.1f}]"


