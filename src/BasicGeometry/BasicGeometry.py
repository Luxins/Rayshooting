from dataclasses import dataclass
from statistics import mean
from math import sqrt
from Ray.Ray import RayInterval, Ray, overlapIntervals
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



def intersect(box: AABB, ray: Ray, rayInterval: RayInterval)-> tuple[bool, RayInterval]:
    """intersect kontrolliert inwiefern das AABB von der Ray getroffen wird.
    Es wird dabei sowohl ein boolean zurückgegeben (wurde getroffen/wurde nicht getroffen).
    Als auch ein Interval (bezüglich t), während dessen die Ray sich in der Box befindet.
    Das zurückgegebene Interval ist notwendigerweise eine Untermenge des Argument-Intervals."""

    # Zuerst computen wir die folgenden Werte:
    y_enter: float = None
    y_exit: float = None
    x_enter: float = None
    x_exit: float = None

    # Handeln der Edge-Cases: Ray direction ist parallel zu Achse(n):
    if ray.direction.y == 0: #Ray bewegt sich nicht in y-Richtung
        if not (box.min.y <= ray.origin.y <= box.max.y): # <=> if the origin's y is not within the bounds of the box, then it will never get there (no progress in y-direction)
            # Keine Intersection möglich:
            return (False, RayInterval(t_enter=float('inf'), t_exit=float('-inf')))
        else: # Wenn die origin sowieso von den y werten in der box liegt
            # ... Dann stimmt der y-Wert für jeden t-wert:
            y_enter: float = float('-inf')
            y_exit: float = float('inf')
        
    # Exakt das gleiche Edge-Case-Handling für x.
    if ray.direction.x == 0: #Ray bewegt sich nicht in x-Richtung
        if not(box.min.x <= ray.origin.x <= box.max.x): # ... origin.x nicht dazwischen...
            # => keine Intersection möglich:
            return (False, RayInterval(t_enter=float('inf'), t_exit=float('-inf')))
        else: # origin.x dazwischen
            x_enter: float = float('-inf')
            x_exit: float = float('inf')
     
    # Nach den Edge cases sind wir nun garantiert:
    # Entweder nicht mehr parallel zur Achse,
    # oder wir sind sowieso in den x bzw. y bounds der box.

    # Nun ist die Frage, nicht mehr ob x_enter/y_enter existiert, sondern was deren Werte sind.
    # Wir suchen nach einem t Wert gegeben haben wir x bzw. y Werte.
    # Dementsprechend suchen wir dt/dx.
    # Bilden wir dx/dt und invertieren dann...

    if x_enter is None and x_exit is None: # x_enter was not already set by edge case handling
        dt_dx: float = 1 / ray.direction.x # dt_dy bedeutet dt/dy
        
        dx_enter: float = (box.min.x - ray.origin.x) # Note: dx kann negativ sein
        dx_exit: float = (box.max.x - ray.origin.x)
        x_enter = dx_enter * dt_dx
        x_exit = dx_exit * dt_dx

        x_enter, x_exit = min(x_enter, x_exit), max(x_enter, x_exit)

    valid_range_x: RayInterval = RayInterval(
        x_enter,
        x_exit
    )

    if y_enter is None and y_exit is None:
        dt_dy: float = 1 / ray.direction.y


        dy_enter: float = (box.min.y - ray.origin.y)
        dy_exit: float = (box.max.y - ray.origin.y)
        y_enter = dy_enter * dt_dy
        y_exit = dy_exit * dt_dy

        y_enter, y_exit = min(y_enter, y_exit), max(y_enter, y_exit)

    valid_range_y: RayInterval = RayInterval(
        y_enter,
        y_exit
    )

    # Wir haben nun jeweils ein konkretes t-interval berechnet wo der x- bzw. y-Wert in der Box liegt.
    # Nun ist die Frage, ob die Intervalle sich überschneiden.
    # Wenn ja, dann ist die Schnittmenge ein Interval von t, in welchem die Ray innerhalb der Box liegt.
    schnittInterval: Optional[RayInterval] = overlapIntervals(
        valid_range_x,
        valid_range_y
    )

    if schnittInterval is None:
        return False, RayInterval(
            t_enter=float("inf"),
            t_exit=float("-inf")
        )

    schnittInterval = overlapIntervals(
        schnittInterval,
        rayInterval # Durch das Overlapping mit dem Argument interval können hits für negative t-Werte gefiltert werden!
    )

    if schnittInterval is None:
        return False, RayInterval(
            t_enter=float("inf"),
            t_exit=float("-inf")
        )

    return True, schnittInterval

