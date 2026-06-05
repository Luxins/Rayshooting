from SpatialPartitioners.Quadtree.Quadtree import Quadtree
from AABBDistribution.AABBDistribution import AABBDistribution
from Ray.Ray import Ray
from BasicGeometry.BasicGeometry import Vec2
from Ray.Ray import RayHit

QUADTREE_LAYERS: int = 5 # 5 Layers entspricht 4 ** 5 = 1024 Paritionen

if __name__ == "__main__":
    # Die momentane Main läuft headless.
    # D.h. das Zeug wird nicht in PyGame gerendert
    # RayShooting wird aber trotzdem korrekt durchgeführt.
    # Das Pygame window was sich kurz öffnet kommt daher, dass ich ein globales Singleton für Pygame instanziiere.
    
     # Tatsächlich ist die Anzahl der Partikel für räumliche Partitioniernug egal.
     # Weil wir zerlegen ja den Raum an sich und nicht die Menge der Partikel wie bei den BVH
    scene: AABBDistribution = AABBDistribution(20)
    tree: Quadtree = Quadtree(scene, layers=QUADTREE_LAYERS)

    # Jetzt bauen wir uns eine Ray mit Origin irgendwo im Grid, um rayshooting auszuführen
    root = tree.nodes[0]
    ray: Ray = Ray(
        origin=Vec2(
            x=root.bounds.min.x + 30, 
            y=root.bounds.min.y + 30
        ),
        direction=Vec2(
            1,1
        )
    )

    # 'RayHit' enthält zusätzlich auch Informationen, wann die Ray die Parition getroffen hat.
    partitionsHit: list[RayHit] = tree.shootRay(ray)