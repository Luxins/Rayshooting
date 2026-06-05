import pygame
from dataclasses import dataclass, field
from collections.abc import Callable
from BasicGeometry.BasicGeometry import AABB, Vec2, VecInt2
from Ray.Ray import Ray

from typing import TYPE_CHECKING

# Diese Klasse ist dafür da ein visuelles Flipbook der Parittionierungsmethoden zu erschaffen


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
DEFAULT_CIRCLE_COLOR = (0, 255, 0) # Green
DEFAULT_LINE_COLOR = (150, 0, 40) # Some color...

DEFAULT_NODE_FILL_COLOR = (100, 180, 255, 60)  # RGBA, alpha: 0 transparent, 255 opaque


from distinctipy import distinctipy



@dataclass
class Loop:
    running: bool = False

    # The offset vector value gets added onto everything that is displayed, such that the simulation is centered in the window
    # We calculate the actual offset in centerSimulationInWindow()
    # The offset can not be precomputed, as simulation size is dynamic and we do not want to have tight coupeling between the classes.
    offset: Vec2 = field(default_factory=Vec2)
    
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

    rays: list[Ray] = field(default_factory=list)

    # The state Chain is traversable like a flipbook.
    stateChain: list[AABB] = field(default_factory=list)
    # The index is mutated in the .run() method, to enable flip book like behaviour
    indexInStateChain: int = 0

    def __post_init__(self):
        """As the pygame stuff can not be covered by a dataclass"""
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(WINDOW_SIZE)
        self.clock: pygame.time.Clock = pygame.time.Clock()


    def addObject(self, obj: AABB) -> None:
        self.objects.append(obj)
    
    def addRay(self, ray: Ray)-> None:
        self.rays.append(ray)

    def addNodeBoundToFlipbook(self, node: AABB, skip: bool) -> None:
        """Later you can look at the state changes like a flipbook"""
        # skip means that we flip ahead right away when encountering the flipbook page
        node.skip = skip
        self.stateChain.append(node)
            
    
    def run(self):
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
            
            # If we are in a skipable range of the stateChain, increase the index up until the objects are no longer skipable
            while self.indexInStateChain < len(self.stateChain) and self.stateChain[self.indexInStateChain].skip:
                self.indexInStateChain += 1


            # 2. Update state
            # No need for that, as we collected all state before calling .run()

            # 3. Clear screen
            self.screen.fill((30, 30, 30))

            # Draw all the constant objects:
            for obj in self.objects:
                self.drawObjWithOffset(obj)
            # Draw all the things in the flipbook up to the current index
            for i in range(0, self.indexInStateChain):
                nodeBound: AABB = self.stateChain[i]
                self.drawNodeBoundWithOffset(nodeBound)
            
            # Draw all the points (e.g. ray origins):
            for ray in self.rays:
                self.drawRayWithOffset(ray)

            # 5. Present state:
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
    
    def drawRayWithOffset(self, ray: Ray) -> None:
        # First of all converting the logical coordinates to pygame...
        start_point: Vec2 = ray.origin * SIMULATION_SCAlAR + self.offset
        end_point: Vec2 = ray.direction.normalize() * 2000 + self.offset

        pygame_start_point: VecInt2 = VecInt2(
            x=round(start_point.x),
            y=round(start_point.y)
        )
        pygame_end_point: VecInt2 = VecInt2(
            x=round(end_point.x),
            y=round(end_point.y)
        )
        pygame.draw.circle(self.screen, DEFAULT_CIRCLE_COLOR, (pygame_start_point.x, pygame_start_point.y), radius=5)
        pygame.draw.line(self.screen, DEFAULT_LINE_COLOR, (pygame_start_point.x, pygame_start_point.y), (pygame_end_point.x, pygame_end_point.y), width=5)

    def drawObjWithOffset(self, obj: AABB) -> None:
        rect = self.aabbToPygameRect(obj, self.offset)
        pygame.draw.rect(self.screen, DEFAULT_OBJECT_COLOR, rect, width=0)

    def drawNodeBoundWithOffset(self, obj: AABB) -> None:
        rect = self.aabbToPygameRect(obj, self.offset)
        if obj.shade:
            # Create transparent surface with same size as rect
            fill_surface = pygame.Surface(rect.size, pygame.SRCALPHA)

            # Fill the local surface
            fill_surface.fill(DEFAULT_NODE_FILL_COLOR)

            # Draw transparent fill onto screen
            self.screen.blit(fill_surface, rect.topleft)
        pygame.draw.rect(self.screen, DEFAULT_NODE_BOUND_COLOR, rect, width=3)

    def centerSimulationInWinow(self, simulation: "AABBDistribution"):
        simulation_center: Vec2 = simulation.calculateSimulationCenter()
        self.offset = WINDOW_CENTER - simulation_center * SIMULATION_SCAlAR



loopSingleton: Loop = Loop()