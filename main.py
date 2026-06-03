from SpatialPartitioners.Quadtree.Quadtree import Quadtree
from AABBDistribution.AABBDistribution import AABBDistribution

QUADTREE_LAYERS: int = 5 # 5 Layers entspricht 4 ** 5 = 1024 Paritionen

if __name__ == "__main__":
     # Tatsächlich ist die Anzahl der Partikel für räumliche Partitioniernug egal.
     # Weil wir zerlegen ja den Raum an sich und nicht die Menge der Partikel wie bei den BVH
    scene: AABBDistribution = AABBDistribution(20)
    tree: Quadtree = Quadtree(scene, layers=QUADTREE_LAYERS)
