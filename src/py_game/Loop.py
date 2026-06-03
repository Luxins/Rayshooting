import pygame
from dataclasses import dataclass, field
from collections.abc import Callable
from BasicGeometry.BasicGeometry import AABB, Vec2
from SpatialPartitioners.Quadtree.QuadtreeNode import QuadtreeNode

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from AABBDistribution.AABBDistribution import AABBDistribution

SIMULATION_SCAlAR = 7 # The simulation works in 100 x 100, if we use 7 we can still se boundary issues

WINDOW_SIDE_LENGTH: int = 800
WINDOW_SIZE: tuple[int, int] = (WINDOW_SIDE_LENGTH, WINDOW_SIDE_LENGTH)
WINDOW_CENTER: Vec2 = Vec2(
    x=WINDOW_SIDE_LENGTH/2,
    y=WINDOW_SIDE_LENGTH/2
)

FRAME_RATE: int = 60
DEFAULT_OBJECT_COLOR = (255, 255, 255) # White
DEFAULT_NODE_BOUND_COLOR = (255, 0, 0) # Red

from distinctipy import distinctipy

def generate_pygame_colors(n: int) -> list[tuple[int, int, int]]:
    """Generates n different colors that are as different as possible"""
    colors_float = distinctipy.get_colors(n)

    return [
        (
            int(r * 255),
            int(g * 255),
            int(b * 255),
        )
        for r, g, b in colors_float
    ]

@dataclass
class Loop:
    running: bool = False
    eventCallbacks: list[Callable[["Loop", pygame.event.Event], None]] = field(default_factory=list)

    # This flag determines whether bounding boxes or objects are drawn first:
    objectsInBackground: bool = True

    # This vector value gets added onto everything that is displayed, such that the simulation is centered in the window
    # We calculate the actual offset in centerSimulationInWindow()
    # The offset can not be precomputed, as simulation size is dynamic and we do not want to have tight coupeling between the classes.
    offset: Vec2 = field(default_factory=Vec2)
    colors: list[tuple[int, int, int]] = field(default_factory=list)
    
    # This function is needed to AABB -> pygame.Rect
    @staticmethod
    def aabbToPygameRect(aabb: AABB, offset: Vec2 = Vec2()) -> pygame.Rect:
        left = round(aabb.min.x * SIMULATION_SCAlAR + offset.x)
        top = round(aabb.min.y * SIMULATION_SCAlAR + offset.y)
        right = round(aabb.max.x * SIMULATION_SCAlAR + offset.x)
        bottom = round(aabb.max.y * SIMULATION_SCAlAR + offset.y)

        return pygame.Rect(
            left,
            top,
            right - left,
            bottom - top,
        )

    # The objects will always be rendered and can not be flipped like a flipbook:
    objects: list[AABB] = field(default_factory=list)

    # The state Chain is traversable like a flipbook.
    stateChain: list[QuadtreeNode | AABB] = field(default_factory=list)
    # The index is mutated in the .run() method, to enable flip book like behaviour
    indexInStateChain: int = 0

    def __post_init__(self):
        """As the pygame stuff can not be covered by a dataclass"""
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(WINDOW_SIZE)
        self.clock: pygame.time.Clock = pygame.time.Clock()

    
    def addCallback(self, callback: Callable[["Loop", pygame.event.Event], None]):
        self.eventCallbacks.append(callback)

    def addNodes(self, nodes: QuadtreeNode | AABB) -> None:
        self.objects.append(nodes)

    def addNodeToFlipbook(self, node: QuadtreeNode) -> None:
        """Later you can look at the state changes like a flipbook"""
        self.stateChain.append(node.bounds)
            

    
    def run(self):
        self.colors = generate_pygame_colors(len(self.stateChain)) # For each node bound we want to have a different color
        self.running: bool = True
        while self.running:
            # 1. Handling events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT: # Left arrow key, flip the flipbook backwards
                        if self.indexInStateChain > 0:
                            self.indexInStateChain -= 1
                    if event.key == pygame.K_RIGHT: # Right arrow key, flip the flibook to the front
                        if self.indexInStateChain < len(self.stateChain):
                            self.indexInStateChain += 1
                for eventCallback in self.eventCallbacks:
                    eventCallback(self, event)
            
            # 2. Update state
            # No need for that, as we collected all state before calling .run()

            # 3. Clear screen
            self.screen.fill((30, 30, 30))

            # 4. Draw stuff
            if self.objectsInBackground:
                # Draw all the constant objects:
                for obj in self.objects:
                    self.drawObjWithOffset(obj)
                # Draw all the things in the flipbook up to the current index
                for i in range(0, self.indexInStateChain):
                    node: QuadtreeNode | AABB = self.stateChain[i]
                    self.drawNodeWithOffset(node, color=self.colors[i])
            elif not self.objectsInBackground:
                # Draw all the things in the flipbook up to the current index
                for i in range(0, self.indexInStateChain):
                    node: QuadtreeNode | AABB = self.stateChain[i]
                    self.drawNodeWithOffset(node, color=self.colors[i])

                # Draw all the constant objects:
                for obj in self.objects:
                    self.drawObjWithOffset(obj)

            # 5. Present state:
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def drawObjWithOffset(self, node: QuadtreeNode | AABB) -> None:
        converted: AABB = None
        if isinstance(node, AABB):
            converted = node
        elif isinstance(node, QuadtreeNode):
            converted = node.bounds

        rect = self.aabbToPygameRect(converted, self.offset)
        pygame.draw.rect(self.screen, DEFAULT_OBJECT_COLOR, rect, width=0)

    def drawNodeWithOffset(self, node: QuadtreeNode | AABB, color: tuple[int, int, int]) -> None:
        converted: AABB = None
        if isinstance(node, AABB):
            converted = node
        elif isinstance(node, QuadtreeNode):
            converted = node.bounds
    
        rect = self.aabbToPygameRect(converted, self.offset)
        pygame.draw.rect(self.screen, color, rect, width=3)

    def centerSimulationInWinow(self, simulation: "AABBDistribution"):
        simulation_center: Vec2 = simulation.calculateSimulationCenter()
        self.offset = WINDOW_CENTER - simulation_center * SIMULATION_SCAlAR



loopSingleton: Loop = Loop()