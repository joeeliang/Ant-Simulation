from math import pi, sin, cos, atan2, radians, degrees
import random
import pygame
import numpy as np
from pygame.sprite import AbstractGroup
import os

WIDTH = 1200
HEIGHT = 800
FPS = 60
PHERO_RATIO = 5  # downscaling factor for pheromone layer

class PheroMap:
    def __init__(self, width, height):
        self.width = width // PHERO_RATIO
        self.height = height // PHERO_RATIO
        self.home_pheromone = np.zeros((self.height, self.width))
        self.food_pheromone = np.zeros((self.height, self.width))
        self.evaporation_rate = 0.995
        self.diffusion_rate = 0.1

    def update(self):
        # Evaporation
        self.home_pheromone *= self.evaporation_rate
        self.food_pheromone *= self.evaporation_rate
        
        # Diffusion
        self.home_pheromone = self.diffuse(self.home_pheromone)
        self.food_pheromone = self.diffuse(self.food_pheromone)

    def diffuse(self, pheromone):
        return pheromone + self.diffusion_rate * (
            np.roll(pheromone, 1, axis=0) + 
            np.roll(pheromone, -1, axis=0) + 
            np.roll(pheromone, 1, axis=1) + 
            np.roll(pheromone, -1, axis=1) - 
            4 * pheromone
        )

    def add_pheromone(self, pos, pheromone_type, amount):
        x, y = int(pos[0] // PHERO_RATIO), int(pos[1] // PHERO_RATIO)
        if 0 <= x < self.width and 0 <= y < self.height:
            if pheromone_type == 'home':
                self.home_pheromone[y, x] += amount
            elif pheromone_type == 'food':
                self.food_pheromone[y, x] += amount

    def get_pheromone(self, pos, pheromone_type):
        x, y = int(pos[0] // PHERO_RATIO), int(pos[1] // PHERO_RATIO)
        if 0 <= x < self.width and 0 <= y < self.height:
            if pheromone_type == 'home':
                return self.home_pheromone[y, x]
            elif pheromone_type == 'food':
                return self.food_pheromone[y, x]
        return 0

class Ant(pygame.sprite.Sprite):
    def __init__(self, drawing_surface, phero_map, home, food_sources):
        super().__init__()
        self.phero_map = phero_map
        self.drawing_surface = drawing_surface
        self.home = home
        self.food_sources = food_sources
        self.width, self.height = self.drawing_surface.get_size()
        self.image = pygame.Surface((12, 21)).convert()
        self.image.set_colorkey(0)
        self.color = (100, 42, 42)
        self.rect = self.image.get_rect(center=self.home)
        self.draw_ant()
        self.pos = np.array(self.rect.center, dtype=float)
        self.vel = np.array([0.0, 0.0])
        self.angle = 0
        self.state = 'seeking_food'
        self.max_speed = 2
        self.wander_strength = 0.3
        self.pheromone_strength = 0.5
        self.pheromone_deposit_rate = 0.5

    def draw_ant(self):
        pygame.draw.ellipse(self.image, self.color, [3, 2, 6, 6])
        pygame.draw.ellipse(self.image, self.color, [4, 6, 4, 9])
        pygame.draw.ellipse(self.image, self.color, [3, 13, 6, 8])
        pygame.draw.aaline(self.image, self.color, [0, 5], [11, 15])
        pygame.draw.aaline(self.image, self.color, [0, 15], [11, 5])
        pygame.draw.aaline(self.image, self.color, [0, 10], [12, 10])
        pygame.draw.aaline(self.image, self.color, [2, 0], [4, 3])
        pygame.draw.aaline(self.image, self.color, [9, 0], [7, 3])

    def update(self):
        self.move()
        self.check_boundaries()
        self.deposit_pheromone()
        self.check_food_home()
        self.rect.center = self.pos

    def move(self):
        # Wander
        wander_angle = self.angle + random.uniform(-pi/4, pi/4)
        wander_dir = np.array([cos(wander_angle), sin(wander_angle)])
        
        # Follow pheromones
        pheromone_dir = self.get_pheromone_direction()
        
        # Combine movements
        direction = wander_dir * self.wander_strength + pheromone_dir * self.pheromone_strength
        direction = direction / np.linalg.norm(direction)
        
        self.vel = direction * self.max_speed
        self.pos += self.vel
        self.angle = atan2(self.vel[1], self.vel[0])
        
        # Rotate ant image
        self.image = pygame.transform.rotate(self.image, -degrees(self.angle))
        self.rect = self.image.get_rect(center=self.rect.center)

    def get_pheromone_direction(self):
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        pheromone_type = 'food' if self.state == 'seeking_food' else 'home'
        max_pheromone = 0
        best_dir = np.array([0.0, 0.0])
        
        for dx, dy in directions:
            new_pos = self.pos + np.array([dx, dy]) * PHERO_RATIO
            pheromone = self.phero_map.get_pheromone(new_pos, pheromone_type)
            if pheromone > max_pheromone:
                max_pheromone = pheromone
                best_dir = np.array([dx, dy])
        
        return best_dir

    def check_boundaries(self):
        self.pos[0] = max(0, min(self.pos[0], self.width))
        self.pos[1] = max(0, min(self.pos[1], self.height))

    def deposit_pheromone(self):
        pheromone_type = 'home' if self.state == 'returning_home' else 'food'
        self.phero_map.add_pheromone(self.pos, pheromone_type, self.pheromone_deposit_rate)

    def check_food_home(self):
        if self.state == 'seeking_food':
            for food in self.food_sources:
                if np.linalg.norm(self.pos - food) < 20:
                    self.state = 'returning_home'
                    break
        elif self.state == 'returning_home':
            if np.linalg.norm(self.pos - self.home) < 20:
                self.state = 'seeking_food'

class FoodSource(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(center=pos)

def main():
    pygame.init()
    pygame.display.set_caption("Ant Colony Optimization")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    phero_map = PheroMap(WIDTH, HEIGHT)
    home = (WIDTH // 2, HEIGHT // 2)
    food_sources = [
        (100, 100),
        (WIDTH - 100, 100),
        (100, HEIGHT - 100),
        (WIDTH - 100, HEIGHT - 100)
    ]

    ants = pygame.sprite.Group()
    for _ in range(50):
        ants.add(Ant(screen, phero_map, home, food_sources))

    food_sprites = pygame.sprite.Group()
    for food_pos in food_sources:
        food_sprites.add(FoodSource(food_pos))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        screen.fill((255, 255, 255))
        
        # Update and draw pheromone map
        phero_map.update()
        pheromone_surface = pygame.Surface((WIDTH, HEIGHT))
        pheromone_surface.fill((255, 255, 255))
        for y in range(phero_map.height):
            for x in range(phero_map.width):
                home_intensity = min(255, int(phero_map.home_pheromone[y, x] * 5))
                food_intensity = min(255, int(phero_map.food_pheromone[y, x] * 5))
                color = (home_intensity, food_intensity, 0)
                pygame.draw.rect(pheromone_surface, color, (x * PHERO_RATIO, y * PHERO_RATIO, PHERO_RATIO, PHERO_RATIO))
        screen.blit(pheromone_surface, (0, 0), special_flags=pygame.BLEND_MULT)

        # Update and draw ants
        ants.update()
        ants.draw(screen)

        # Draw food sources
        food_sprites.draw(screen)

        # Draw home
        pygame.draw.circle(screen, (255, 0, 0), home, 20)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    main()