from AABBDistribution.AABBDistribution import AABBDistribution
from BasicGeometry.BasicGeometry import Vec2, AABB
from SpatialPartitioners.Quadtree.QuadtreeNode import QuadtreeNode
import pygame
from py_game.Loop import loopSingleton
from Ray.Ray import Ray, RayHit

from textwrap import indent

class Quadtree:
    def __init__(self, scene: AABBDistribution, layers: int = 1):
        # Metadata
        self.layers: int = layers
        self.scene: AABBDistribution = scene
        
        # build Recursive is creating the octree structure
        # The goal is to populate self.nodes
        self.nodes: list[QuadtreeNode] = []
        # We need these variables initialized to start the recursion:
        # In order to build the root node, we need a bound for all the objects in the simulation:
        boundOfAllObjects: AABB = AABB.mergeMany(scene.samples)
        initialCenter: Vec2 = boundOfAllObjects.center

        # Figure out the biggest side of a potential square:
        diffX: float = boundOfAllObjects.max.x - boundOfAllObjects.min.x
        diffY: float = boundOfAllObjects.max.y - boundOfAllObjects.min.y

        quarterStep: float = diffX / 4
        if (diffY > diffX):
            quarterStep = diffY / 4
        
        self.buildRecursive(initialCenter, quarterStep, layers)

        # later on, we will assign the objects to the lowest cell that fully contains them.
        self.objects: list[AABB] = self.scene.samples
        self.assignObjectsToCells(self.objects, cellIndex=0)
        
    def assignObjectsToCells(self, objects: list[AABB], cellIndex: int):

        for obj in objects:
            self.assignObjectToCell(obj, cellIndex)
    
    def assignObjectToCell(self, obj: AABB, cellIndex: int):
        # You may assume that all objects are contained in the root cell (cellIndex = 0)
        # Hence, let's get the children right away
        children: list[QuadtreeNode] = self.nodes[cellIndex * 4 + 1: cellIndex * 4 + 4]
        # Note: cellIndex * 4 + 1 is a way to refer to the children of cellIndex directly, if you build the entire tree in one go (compare to C.Ericson)

        for child in children:
            if (child.fullyContains(obj)):
                return self.assignObjectToCell(obj, child.myIndex)
        
        # If execution flow reaches this line, no further child fully contains the object
        # Hence the current cell can take ownership of the object.
        currentCell: QuadtreeNode = self.nodes[cellIndex]
        currentCell.takeOwnership(obj)
                    
    
    def buildRecursive(self, center: Vec2, quarterStep: float, layer: int):
        if (layer == 0):
            return -1
        
        nodeBounds: AABB = AABB(Vec2(center.x - quarterStep * 2,\
        center.y - quarterStep * 2), Vec2(center.x + quarterStep * 2, center.y + quarterStep * 2))

        node: QuadtreeNode = QuadtreeNode(len(self.nodes), nodeBounds, center)
        self.nodes.append(node)
        # Setting the new center values
        upper_left: Vec2 = Vec2(center.x - quarterStep, center.y - quarterStep)
        upper_right: Vec2 = Vec2(center.x + quarterStep, center.y - quarterStep)
        lower_right: Vec2 = Vec2(center.x + quarterStep, center.y + quarterStep)
        lower_left: Vec2 = Vec2(center.x - quarterStep, center.y + quarterStep)

        # The node itself is already fully defined, just the kids aren't yet.
        # To keep the order of display, we can already add it to the flipbook

        loopSingleton.addNodeBoundToFlipbook(node.bounds, skip=True) #... This test verified, that the quadtree construction works
        

        node.setChildren(
            [
                self.buildRecursive(upper_left, quarterStep/2, layer - 1),
                self.buildRecursive(upper_right, quarterStep/2, layer - 1),
                self.buildRecursive(lower_right, quarterStep/2, layer - 1),
                self.buildRecursive(lower_left, quarterStep/2, layer - 1)
            ]
        )

        return node.myIndex

    def __str__(self):
        metadata: str = f"Number of Nodes:\t{len(self.nodes)}\nRoot Node bounds:\n{indent(self.nodes[0].bounds.__str__(), '\t')}"
        node_data: str = "\n\n".join(str(node) for node in self.nodes)
        return f"{metadata}\n\n{node_data}"
    
    ### Ab hier folgen nun die Methoden für die Query ###
    ### Gegeben eine Ray, wollen wir so schnell wie möglich alle Partitionen des Quadtrees zurückgeben,
    ### die von der Ray getroffen werden

    def shootRay(self, ray: Ray)-> list[RayHit]:
        # Our shoot Ray is breadth first centered
        queue: list[QuadtreeNode] = [self.nodes[0]]

        containsOrign: list[QuadtreeNode] = self.listNodesWithOrigin(ray)

        # Alle Elemente in der Queue sind von der gleichen Quadtree-Ebene
        # Wir wollen nach jenen filtern, die von der Ray getroffen werden.
        # Dafür müssen wir als erstes die Leaf-Partition finden, in der sich der origin der Ray befindet
            
            
        

    def listNodesWithOrigin(self, ray: Ray)-> list[QuadtreeNode]:
        containsOrigin: list[QuadtreeNode] = [] # Auf jeder Ebene wollen wir tracken, welche Node den Origin der Ray enthält. containsOrigin[0] ist die Node der 1-ten Ebene, containsOrign[1] der 2-ten Ebene usw....
        # Unser erstes Zweig traversal O(log n) ist nur dafür da, containsOrigin zu füllen
        # Das Zweig traveral ist also eine Art greedy depth first
        stack: list[QuadtreeNode] = [self.nodes[0]]
        while stack:
            nodeWithOrigin: QuadtreeNode = stack.pop()
            containsOrigin.append(nodeWithOrigin)
            children: list[QuadtreeNode] = [self.nodes[nodeIndex] for nodeIndex in nodeWithOrigin.children]
            for child in children:
                if child.bounds.containsPoint(ray.origin):
                    stack.append(child)
        
        return containsOrigin

if __name__ == '__main__':
    
    # Sufficent test for checking that Quadtree construction works!

    scene: AABBDistribution = AABBDistribution(20)
    loopSingleton.centerSimulationInWinow(scene)
    # for sample in scene.samples:
    #     print(sample, '\n')
    tree: Quadtree = Quadtree(scene, 3)
    rootX, rootY = tree.nodes[0].bounds.min.x, tree.nodes[0].bounds.min.y

    ray: Ray = Ray(
        origin=Vec2(
            x=rootX + 30, 
            y=rootY + 30
        ),
        direction=Vec2(
            0,0
        )
    )

    loopSingleton.addPoint(ray.origin)
    
    nodesWithOrigin: list[QuadtreeNode] = tree.listNodesWithOrigin(ray)
    nodesWithOrigin[-1].bounds.shade = True


    # print(tree)
    loopSingleton.run()
