import pygame
import random

# initialize pygame
pygame.init()

# set up some constants
WIDTH, HEIGHT = 800, 600
HOME_COLOR = (255, 0, 0)  # red
FOOD_COLOR = (0, 255, 0)  # green
TRAIL_COLOR = (255, 255, 0)  # yellow
ANT_COLOR = (0, 0, 255)  # blue

# set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# set up the home and food locations
home_x, home_y = WIDTH // 2, HEIGHT // 2
food_x, food_y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)

# set up the ant's initial position and state
ant_x, ant_y = home_x, home_y
has_food = False
trail = []

# game loop
while True:
    # handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # move the ant
    if has_food:
        # move towards home
        dx = home_x - ant_x
        dy = home_y - ant_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance > 1:
            ant_x += dx / distance
            ant_y += dy / distance
        else:
            has_food = False
            trail = []
    else:
        # move towards food
        dx = food_x - ant_x
        dy = food_y - ant_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance > 1:
            ant_x += dx / distance
            ant_y += dy / distance
        else:
            has_food = True
            trail.append((ant_x, ant_y))

    # draw everything
    screen.fill((255, 255, 255))  # white background

    # draw home
    pygame.draw.circle(screen, HOME_COLOR, (home_x, home_y), 10)

    # draw food
    pygame.draw.circle(screen, FOOD_COLOR, (food_x, food_y), 10)

    # draw trail
    for x, y in trail:
        pygame.draw.circle(screen, TRAIL_COLOR, (int(x), int(y)), 2)

    # draw ant
    pygame.draw.circle(screen, ANT_COLOR, (int(ant_x), int(ant_y)), 5)

    # update the screen
    pygame.display.flip()
    pygame.time.Clock().tick(60)