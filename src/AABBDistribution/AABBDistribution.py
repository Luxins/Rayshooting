from math import sqrt

from BasicGeometry.BasicGeometry import AABB, Vec2
import random
from py_game.Loop import loopSingleton

# Define some arbitrary constants:
PARTICLE_SIZE: int = 4

class AABBDistribution:
    def __init__(self,number_of_particles: int):
        self.SIMULATION_SIZE = sqrt((number_of_particles * 36)/0.08)
        self.number_of_particles = number_of_particles
        self.samples: list[AABB] = []

        for _ in range(self.number_of_particles):
            x_upper_left: float = random.uniform(0.0, self.SIMULATION_SIZE - PARTICLE_SIZE)
            y_upper_left: float = random.uniform(0.0, self.SIMULATION_SIZE - PARTICLE_SIZE)

            particle: AABB = AABB(
                Vec2(x_upper_left, y_upper_left),
                Vec2(x_upper_left + PARTICLE_SIZE, y_upper_left + PARTICLE_SIZE)
            )

            self.samples.append(particle)
            loopSingleton.addNodes(particle)
        
        self.simulation_center: Vec2 = self.calculateSimulationCenter()

    def calculateSimulationCenter(self)-> Vec2:
        return Vec2(
            x=self.SIMULATION_SIZE/2,
            y=self.SIMULATION_SIZE/2
        )



# Sanity check
if __name__ == '__main__':
    print('yeet')
    dist: AABBDistribution = AABBDistribution(10)
    print(dist.samples)