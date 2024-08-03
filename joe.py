from math import pi, sin, cos, atan2, radians, degrees
from random import randint
import pygame
import numpy as np
from pygame.sprite import AbstractGroup
import os

WIDTH = 1200
HEIGHT = 800
FPS = 60
PHERO_RATIO = 5 #downscaling factor for pheromone layer

class Ant(pygame.sprite.Sprite):
    def __init__(self,drawing_surface, pheroLayer, home):
        super().__init__()
        self.pheroLayer = pheroLayer
        self.drawing_surface = drawing_surface
        self.home = home
        self.width, self.height = self.drawing_surface.get_size()
        self.pheroSize = (int(self.width)/PHERO_RATIO, int(self.height)/PHERO_RATIO)
        self.image = pygame.Surface((12, 21)).convert()
        self.image.set_colorkey(0)
        self.color = (100, 42, 42)
        self.rect = self.image.get_rect(center=self.home)
        self.draw_ant()
        self.pos = np.array(self.rect.center)
        self.acc = np.array([0,0])
        self.vel = np.array([0,0])

        self.desired_velocity = np.array([0,0])
        self.desire_direction = np.array([0,0])
        self.maxSpeed = 5
        self.steerStr = 0.1
        self.wandrStr = 0.1
        self.dt = 1 / 60 
    
    def draw_ant(self): # Need to modify later, else its plagarism.
        
        pygame.draw.aaline(self.image, self.color, [0, 5], [11, 15])
        pygame.draw.aaline(self.image, self.color, [0, 15], [11, 5])
        pygame.draw.aaline(self.image, self.color, [0, 10], [12, 10])
        pygame.draw.aaline(self.image, self.color, [2, 0], [4, 3])
        pygame.draw.aaline(self.image, self.color, [9, 0], [7, 3])
        pygame.draw.ellipse(self.image, self.color, [3, 2, 6, 6])
        pygame.draw.ellipse(self.image, self.color, [4, 6, 4, 9])
        pygame.draw.ellipse(self.image, self.color, [3, 13, 6, 8])

    def update(self):
        random_angle = randint(0,360)
        random_direction = np.array([cos(radians(random_angle)),sin(radians(random_angle))])
        self.desire_direction += random_direction
        self.pos += self.vel
        self.rect.center = self.pos

def main():
    pygame.init()
    pygame.display.set_caption("Ants")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    ants = pygame.sprite.Group()
    first_ant = Ant(screen, None, (100,100))
    ants.add(first_ant)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                running = False

        screen.fill((255, 255, 255))
        ants.draw(screen)
        ants.update()
        pygame.display.update()

        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    main()