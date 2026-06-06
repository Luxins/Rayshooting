from BasicGeometry.BasicGeometry import Vec2, AABB
from dataclasses import dataclass
from typing import Optional


class Ray:
    def __init__(self, origin=Vec2, direction=Vec2, min_t: float = 0, max_t: float = float('inf')):
        self.origin: Vec2 = origin
        self.direction: Vec2 = direction
        self.min_t: float = min_t
        # max_t < infinity means that the ray is used as a finite ray segment.
        self.max_t: float = max_t

    def PointAt(self, t: float)-> Vec2:
        return self.origin + self.direction * t


@dataclass
class RayHit:
    """Provides a shared contract. Space Partitioners return a list of RayHits when queried for ray-shooting.
    A RayHit indicates the Partition (AABB) that was hit, as well as the point of time at which the ray first intersects with that partition intersection_t"""
    partition: AABB
    t_enter: float
    t_exit: float


@dataclass
class RayInterval:
    t_enter: float
    t_exit: float





def overlapIntervals(
    a: RayInterval,
    b: RayInterval
) -> Optional[RayInterval]:

    t_enter = max(a.t_enter, b.t_enter)
    t_exit = min(a.t_exit, b.t_exit)

    if t_enter > t_exit:
        return None

    return RayInterval(t_enter, t_exit)




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
