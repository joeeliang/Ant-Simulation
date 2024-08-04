from math import pi, sin, cos, atan2, radians, degrees
from random import randint
import random
import pygame
import numpy as np
from pygame.sprite import AbstractGroup
import os

WIDTH = 1000
HEIGHT = 800
FPS = 60
PHERO_RATIO =5  # downscaling factor for pheromone layer
PHERO_SIZE = 10  # size of each pheromone pixel in the pheromone map
NUM_ANTS = 100

def convert_to_phero(pos):
    '''Converts real coordinates to Pheromap coordinates'''
    x, y = int(pos[0] // PHERO_RATIO), int(pos[1] // PHERO_RATIO)
    return (x, y)

class Ant(pygame.sprite.Sprite):
    def __init__(self,drawing_surface, pheroLayer, home, screen):
        super().__init__()
        self.pheroLayer = pheroLayer
        self.max_speed = 4a
        self.trail_strength = 3
        self.avoidance_strength = 1
        self.got_food_time = None
        self.pheromone_strength = 2
        self.screen = screen
        self.drawing_surface = drawing_surface
        self.steer_strength = 1
        self.home = home
        self.home_rect = pygame.Rect(self.home[0] - 15, self.home[1] - 15, 30, 30)
        self.width, self.height = self.drawing_surface.get_size()
        self.pheroSize = (int(self.width)/PHERO_RATIO, int(self.height)/PHERO_RATIO)
        self.image = pygame.Surface((12, 21)).convert()
        self.image.set_colorkey(0)
        self.rect = self.image.get_rect(center=self.home)
        self.wander_strength = 0.4
        self.draw_ant()
        self.state = 'seeking_food'
        self.pos = np.array(self.rect.center,dtype='float64')
        self.vel =  np.array([random.uniform(-1,1),random.uniform(-1,1)])
        self.desire_direction = np.array([random.uniform(-1,1),random.uniform(-1,1)])
        self.orig_img = pygame.transform.rotate(self.image.copy(), -90)
        self.pheroTrail = set()
    
    def draw_ant(self): # Need to modify later, else its plagarism.
        color = (100, 42, 42)
        pygame.draw.aaline(self.image, color, [0, 5], [11, 15])
        pygame.draw.aaline(self.image, color, [0, 15], [11, 5])
        pygame.draw.aaline(self.image, color, [0, 10], [12, 10])
        pygame.draw.aaline(self.image, color, [2, 0], [4, 3])
        pygame.draw.aaline(self.image, color, [9, 0], [7, 3])
        pygame.draw.ellipse(self.image, color, [3, 2, 6, 6])
        pygame.draw.ellipse(self.image, color, [4, 6, 4, 9])
        pygame.draw.ellipse(self.image, color, [3, 13, 6, 8])

        if True:
            pygame.draw.ellipse(self.image, color, [0, 5, 3, 3])

    def steer(self,dt,food_list):
        sensor_dir = self.sensors(90, 6, food_list)
        
        # Random movement
        randAng = randint(-180, 180)
        randDir = np.array([cos(radians(randAng)), sin(radians(randAng))])

        # Combine directions
        self.desire_direction = self.desire_direction + sensor_dir + randDir * self.wander_strength

        # Normalize desire_direction
        norm = np.linalg.norm(self.desire_direction)
        if norm > 0:
            self.desire_direction /= np.abs(norm)
        print("After calculation, it is", self.desire_direction)
        
        # Update velocity
        target_vel = self.desire_direction * self.max_speed
        steeringForce = (target_vel - self.vel) * self.steer_strength
        accel = steeringForce if np.linalg.norm(steeringForce) <= self.steer_strength else steeringForce/np.linalg.norm(steeringForce) * self.steer_strength
        self.vel += accel * dt
        
        # Limit velocity to max_speed
        speed = np.linalg.norm(self.vel)
        if speed > self.max_speed:
            self.vel = (self.vel / speed) * self.max_speed

        # Update position
        self.pos += self.vel * dt
        self.rect.center = self.pos.astype(int)

        # Update angle for image rotation
        self.ang = degrees(atan2(self.vel[1], self.vel[0]))
        self.image = pygame.transform.rotate(self.orig_img, -self.ang)
        self.rect = self.image.get_rect(center=self.rect.center)
    
    def detect_collision(self):
        if self.rect.left < 0 or self.rect.right > WIDTH or self.rect.top < 0 or self.rect.bottom > HEIGHT:
            print("AH")
            # Reverse direction
            self.vel = -self.vel
            self.desire_direction = -self.desire_direction

    def is_home(self):
        if self.rect.colliderect(self.home_rect):
            self.state = 'seeking_food' # change state after returning home
            self.wander_strength = 0.1
            self.steer_strength = 5
            self.vel = -self.vel
            self.desire_direction = -self.desire_direction
            self.pheroTrail = set()
            self.desire_direction += self.sensors(360,36)
            norm = np.linalg.norm(self.desire_direction)
            if norm > 0:
                self.desire_direction /= np.abs(norm)

    def is_food(self,food):
        for f in food:
            if self.rect.colliderect(f):
                self.state = 'going_home'
                self.desire_direction += self.sensors(360,36)
                norm = np.linalg.norm(self.desire_direction)
                if norm > 0:
                    self.desire_direction /= np.abs(norm)

    def sensors(self, cone_angle, rays, food=None):
        pheromone_type = 'food' if self.state == 'seeking_food' else 'home'
        best_dir = np.array([0.0, 0.0])
        cone_radius = 15 * PHERO_RATIO
        num_rings = 4
        phero_pos = convert_to_phero(self.pos)

        current_dir = self.vel / (np.linalg.norm(self.vel) + 1e-6)  # Avoid division by zero
        center_angle = atan2(current_dir[1], current_dir[0])

        max_pheromone = 0
        max_pheromone_dir = np.array([0.0, 0.0])

        for ring_distance in np.linspace(2*PHERO_RATIO, cone_radius, num_rings):
            for ang in np.linspace(-cone_angle/2, cone_angle/2, rays):
                dir_angle = center_angle + radians(ang)
                dir = np.array([cos(dir_angle), sin(dir_angle)])
                new_pos = self.pos + dir * ring_distance

                # Draw sensor rays (for visualization)
                # if self.state =="going_home":
                #     pygame.draw.circle(self.screen, (255,255,255), tuple(new_pos.astype(int)), 2)
                #     pygame.draw.line(self.screen, (255,255,255), tuple(self.pos.astype(int)), tuple(new_pos.astype(int)), 1)

                # Pheromone influence
                pheromone = self.pheroLayer.get_pheromone(new_pos, pheromone_type)
                if pheromone > max_pheromone:
                    max_pheromone = pheromone
                    max_pheromone_dir = dir

                # Boundary avoidance
                if new_pos[0] < 0 or new_pos[1] < 0 or new_pos[0] > WIDTH or new_pos[1] > HEIGHT:
                    best_dir -= dir * self.avoidance_strength

                # Trail following
                if self.state == 'going_home' and tuple(convert_to_phero(new_pos)) in self.pheroTrail:
                    print(ang, "has old trail, so", dir)
                    best_dir += dir * self.trail_strength

                # Food following
                if self.state == 'seeking_food' and food:
                     for f in food:
                        if f.rect.collidepoint(new_pos):
                            best_dir += dir * 5
                # Food following
                if self.state == 'going_home':
                    if self.home_rect.collidepoint(new_pos):
                        best_dir += dir * 5


        if self.state == "going_home" and phero_pos in self.pheroTrail:
            self.pheroTrail.remove(phero_pos)
        
        # best_dir += max_pheromone_dir * self.pheromone_strength
        print("from pheromones, ", best_dir)
        best_dir += max_pheromone_dir
        return best_dir

    def update(self, dt, step, food_list):
        self.steer(dt,food_list)
        self.detect_collision()
        if self.state == "going_home":
            self.is_home()
            self.pheroLayer.add_pheromone(self.pos,'food', 0.02)
        if self.state == 'seeking_food':
            self.pheroLayer.add_pheromone(self.pos,'home', 0.02)
            self.is_food(food_list)
            phero_coords = convert_to_phero(self.pos)
            self.pheroTrail.add(phero_coords)

class PheroMap:
    def __init__(self, width, height):
        self.width = width // PHERO_RATIO
        self.height = height // PHERO_RATIO
        self.home_pheromone = np.zeros((self.height, self.width))
        self.food_pheromone = np.zeros((self.height, self.width))
        self.evaporation_rate = 0.8
        self.diffusion_rate = 0.05

    def update(self,step):
        # Evaporation
        if step % 50 == 0:
            self.home_pheromone *= self.evaporation_rate
            self.food_pheromone *= self.evaporation_rate

        self.home_pheromone = np.clip(self.home_pheromone, 0, 1)
        self.food_pheromone = np.clip(self.food_pheromone, 0, 1)

        # Diffusion
        if step % 50 == 0:
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
        x, y = convert_to_phero(pos)
        if 0 <= x < self.width and 0 <= y < self.height:
            if pheromone_type == 'home':
                self.home_pheromone[y, x] += amount
            elif pheromone_type == 'food':
                self.food_pheromone[y, x] += amount

    def get_pheromone(self, pos, pheromone_type):
        x, y = convert_to_phero(pos)
        if 0 <= x < self.width and 0 <= y < self.height:
            if pheromone_type == 'home':
                return self.home_pheromone[y, x]
            elif pheromone_type == 'food':
                return self.food_pheromone[y, x]
        return 0
    
    def draw(self, surface):
        for y in range(self.height):
            for x in range(self.width):
                home_color = int(255 * (self.home_pheromone[y, x]))  
                food_color = int(255 * (self.food_pheromone[y, x]))
                pygame.draw.rect(surface, (home_color, food_color, 0), (x * PHERO_RATIO, y * PHERO_RATIO, PHERO_SIZE, PHERO_SIZE))

class Food(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos
        size = 10
        self.image = pygame.Surface((size, size)) 
        self.rect = self.image.get_rect(center=pos)
        self.image.fill((255, 255, 255))
        pygame.draw.rect(self.image,(0,250,100),self.rect)
        print("here!") 
        
def main():    
    pygame.init()
    pygame.display.set_caption("Ants")
    step = 0
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    food_list = []
    pheromone_map = PheroMap(WIDTH,HEIGHT)
    ants = pygame.sprite.Group()
    food = pygame.sprite.Group()
    home = pygame.Surface((30,30))
    home.fill((255, 255, 2))
    home_rect = home.get_rect(center=(WIDTH/2, HEIGHT/2))
    for n in range(NUM_ANTS):
        ants.add(Ant(screen, pheromone_map, (WIDTH/2,HEIGHT/2), screen))
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mousepos = pygame.mouse.get_pos()
                if event.button == 1: # and pg.Vector2(mousepos).distance_to(nest) > 242:
                    fx = mousepos[0]
                    fy = mousepos[1]
                    food.add(Food((fx,fy)))
                    # draws food
                    food_list.extend(food.sprites()) # extends food list to include new sprites

        screen.fill((255, 255, 255))
        pheromone_map.draw(screen)  # draw pheromone map
        ants.draw(screen)
        food.draw(screen)
        ants.update(0.5, step, food_list)
        pheromone_map.update(step)
        screen.blit(home, home_rect)
        pygame.display.update()
        clock.tick(FPS)
        step += 1

    pygame.quit()

if __name__ == '__main__':
    main()