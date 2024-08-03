#!/usr/bin/env python3
from math import pi, sin, cos, atan2, radians, degrees
from random import randint
import pygame as pg
import numpy as np

'''
NAnts - Ant pheromone trail simulation. Surfarray version. WIP
Copyright (c) 2021  Nikolaus Stromberg  nikorasu85@gmail.com
'''

FLLSCRN = False         # True for Fullscreen, or False for Window
ANTS = 420               # Number of Ants to spawn
WIDTH = 1200            # default 1200
HEIGHT = 800            # default 800
FPS = 600                # 48-90
VSYNC = True            # limit frame rate to refresh rate
PRATIO = 5              # Pixel Size for Pheromone grid, 5 is best

'''Sets variables'''

class Ant(pg.sprite.Sprite):
    '''Class for ants'''
    def __init__(self, drawSurf, nest, pheroLayer):
        super().__init__()
        #self.antID = antNum
        self.drawSurf = drawSurf # drawing surface
        self.curW, self.curH = self.drawSurf.get_size() # height and width
        self.pgSize = (int(self.curW/PRATIO), int(self.curH/PRATIO)) #window size
        self.isMyTrail = np.full(self.pgSize, False) #is my trail
        self.phero = pheroLayer #layer
        self.nest = nest # home location
        self.image = pg.Surface((12, 21)).convert() #creates surface to draw sprite
        self.image.set_colorkey(0) # sets those as transparent
        cBrown = (100,42,42) #colour
        
        # Draw Ant
        pg.draw.aaline(self.image, cBrown, [0, 5], [11, 15])
        pg.draw.aaline(self.image, cBrown, [0, 15], [11, 5]) # legs
        pg.draw.aaline(self.image, cBrown, [0, 10], [12, 10])
        pg.draw.aaline(self.image, cBrown, [2, 0], [4, 3]) # antena l
        pg.draw.aaline(self.image, cBrown, [9, 0], [7, 3]) # antena r
        pg.draw.ellipse(self.image, cBrown, [3, 2, 6, 6]) # head
        pg.draw.ellipse(self.image, cBrown, [4, 6, 4, 9]) # body
        pg.draw.ellipse(self.image, cBrown, [3, 13, 6, 8]) # rear
        # save drawing for later
        self.orig_img = pg.transform.rotate(self.image.copy(), -90) 
        self.rect = self.image.get_rect(center=self.nest) # why does he set center as self. nest??
        self.ang = randint(0, 360) # creates random angle
        self.desireDir = pg.Vector2(cos(radians(self.ang)),sin(radians(self.ang))) # Where it wants to go, stored as a vector
        self.pos = pg.Vector2(self.rect.center)
        self.vel = pg.Vector2(0,0)
        self.last_sdp = (nest[0]/10/2,nest[1]/10/2)
        self.mode = 0 # mode, we can change it into words

    def update(self, dt):  # behavior
        mid_result = left_result = right_result = [0,0,0]
        mid_GA_result = left_GA_result = right_GA_result = [0,0,0] # set result 
        randAng = randint(0,360) #random angle for later use
        accel = pg.Vector2(0,0) # vector for acceleration
        foodColor = (2,150,2)  # color of food to look for, we set global variabesl for this later
        pStrength = 80  # Pheromone strength, evaps slowly, where does he even implement this?
        wandrStr = .12  # how random they walk around. good.
        maxSpeed = 12  # 10-12 seems ok. ok, can change
        steerStr = 3  # 3 or 4, dono. what is this?
        scaledown_pos = (int(self.pos.x/PRATIO), int(self.pos.y/PRATIO)) # Converts ant's current screen coordinates, to smaller resolution of pherogrid.
        #scaledown_pos = (int((self.pos.x/self.curW)*self.pgSize[0]), int((self.pos.y/self.curH)*self.pgSize[1]))
        # Get locations to check as sensor points, in pairs for better detection.
        mid_sensL = Vec2.vint(self.pos + pg.Vector2(21, -3).rotate(self.ang))
        mid_sensR = Vec2.vint(self.pos + pg.Vector2(21, 3).rotate(self.ang))
        left_sens1 = Vec2.vint(self.pos + pg.Vector2(18, -14).rotate(self.ang))
        left_sens2 = Vec2.vint(self.pos + pg.Vector2(16, -21).rotate(self.ang))
        right_sens1 = Vec2.vint(self.pos + pg.Vector2(18, 14).rotate(self.ang))
        right_sens2 = Vec2.vint(self.pos + pg.Vector2(16, 21).rotate(self.ang))
        # May still need to adjust these sensor positions, to improve following.
        # Above code creates coordinate points to look and search for collision points?

        if self.drawSurf.get_rect().collidepoint(mid_sensL) and self.drawSurf.get_rect().collidepoint(mid_sensR): # looks for collision for both sensor pairs
            mid_result, mid_isID, mid_GA_result = self.sensCheck(mid_sensL, mid_sensR)
        if self.drawSurf.get_rect().collidepoint(left_sens1) and self.drawSurf.get_rect().collidepoint(left_sens2):
            left_result, left_isID, left_GA_result = self.sensCheck(left_sens1, left_sens2)
        if self.drawSurf.get_rect().collidepoint(right_sens1) and self.drawSurf.get_rect().collidepoint(right_sens2):
            right_result, right_isID, right_GA_result = self.sensCheck(right_sens1, right_sens2)

        # Uses pygames sprite functions to detect things.
        # .collidepoint checks if coordinate is inside rectangel obstacle. Returns boolean.

        if self.mode == 0 and self.pos.distance_to(self.nest) > 21:
            self.mode = 1 # what?

        elif self.mode == 1:  # Look for food, or trail to food.
            setAcolor = (0,0,100) # sets colour
            if scaledown_pos != self.last_sdp and scaledown_pos[0] in range(0,self.pgSize[0]) and scaledown_pos[1] in range(0,self.pgSize[1]):
                self.phero.img_array[scaledown_pos] += setAcolor
                #self.phero.pixelID[scaledown_pos] = self.antID   # maybe each ant should have their own ID array
                self.isMyTrail[scaledown_pos] = True
                self.last_sdp = scaledown_pos
            if mid_result[1] > max(left_result[1], right_result[1]): #and (mid_result[0],mid_result[2]) == (0,0):
                self.desireDir += pg.Vector2(1,0).rotate(self.ang).normalize()
                wandrStr = .1
            elif left_result[1] > right_result[1]: #and (left_result[0],left_result[2]) == (0,0):
                self.desireDir += pg.Vector2(1,-2).rotate(self.ang).normalize() #left (0,-1)
                wandrStr = .1
            elif right_result[1] > left_result[1]: #and (right_result[0],right_result[2]) == (0,0):
                self.desireDir += pg.Vector2(1,2).rotate(self.ang).normalize() #right (0, 1)
                wandrStr = .1
            if left_GA_result == foodColor and right_GA_result != foodColor :
                self.desireDir += pg.Vector2(0,-1).rotate(self.ang).normalize() #left (0,-1)
                wandrStr = .1
            elif right_GA_result == foodColor and left_GA_result != foodColor:
                self.desireDir += pg.Vector2(0,1).rotate(self.ang).normalize() #right (0, 1)
                wandrStr = .1
            elif mid_GA_result == foodColor: # if food
                self.desireDir = pg.Vector2(-1,0).rotate(self.ang).normalize() #pg.Vector2(self.nest - self.pos).normalize()
                #self.lastFood = self.pos + pg.Vector2(21, 0).rotate(self.ang)
                maxSpeed = 5
                wandrStr = .01
                steerStr = 5
                self.mode = 2

        elif self.mode == 2:  # Once found food, either follow own trail back to nest, or head in nest's general direction.
            setAcolor = (0,80,0)
            if scaledown_pos != self.last_sdp and scaledown_pos[0] in range(0,self.pgSize[0]) and scaledown_pos[1] in range(0,self.pgSize[1]): # ensures these conditions: isnt inside old box, and everything is inside the grid.
                self.phero.img_array[scaledown_pos] += setAcolor # adds colour to the phero map
                self.last_sdp = scaledown_pos # sets the old coordinate to the new coordinate for later
            if self.pos.distance_to(self.nest) < 24:
                #self.desireDir = pg.Vector2(self.lastFood - self.pos).normalize()
                self.desireDir = pg.Vector2(-1,0).rotate(self.ang).normalize() # heads straight home.
                self.isMyTrail[:] = False #np.full(self.pgSize, False) # sets my trial to entirely false
                maxSpeed = 5
                wandrStr = .01 # stops wandering
                steerStr = 5
                self.mode = 1 # sets mode to look for food after deposited food.
            
            elif mid_result[2] > max(left_result[2], right_result[2]) and mid_isID: #and mid_result[:2] == (0,0):
                self.desireDir += pg.Vector2(1,0).rotate(self.ang).normalize()
                wandrStr = .1
            elif left_result[2] > right_result[2] and left_isID: #and left_result[:2] == (0,0):
                self.desireDir += pg.Vector2(1,-2).rotate(self.ang).normalize() #left (0,-1)
                wandrStr = .1
            elif right_result[2] > left_result[2] and right_isID: #and right_result[:2] == (0,0):
                self.desireDir += pg.Vector2(1,2).rotate(self.ang).normalize() #right (0, 1)
                wandrStr = .1
            else:  # maybe first add ELSE FOLLOW OTHER TRAILS?
                self.desireDir += pg.Vector2(self.nest - self.pos).normalize() * .08
                wandrStr = .1   #pg.Vector2(self.desireDir + (1,0)).rotate(pg.math.Vector2.as_polar(self.nest - self.pos)[1])

        wallColor = (50,50,50)  # avoid walls of this color
        if left_GA_result == wallColor:
            self.desireDir += pg.Vector2(0,1).rotate(self.ang) #.normalize()
            wandrStr = .1
            steerStr = 5
        elif right_GA_result == wallColor:
            self.desireDir += pg.Vector2(0,-1).rotate(self.ang) #.normalize()
            wandrStr = .1
            steerStr = 5
        elif mid_GA_result == wallColor:
            self.desireDir += pg.Vector2(-2,0).rotate(self.ang) #.normalize()
            maxSpeed = 5
            wandrStr = .1
            steerStr = 5

        # Avoid edges
        if not self.drawSurf.get_rect().collidepoint(left_sens2) and self.drawSurf.get_rect().collidepoint(right_sens2):
            self.desireDir += pg.Vector2(0,1).rotate(self.ang) #.normalize()
            wandrStr = .01
            steerStr = 5
        elif not self.drawSurf.get_rect().collidepoint(right_sens2) and self.drawSurf.get_rect().collidepoint(left_sens2):
            self.desireDir += pg.Vector2(0,-1).rotate(self.ang) #.normalize()
            wandrStr = .01
            steerStr = 5
        elif not self.drawSurf.get_rect().collidepoint(Vec2.vint(self.pos + pg.Vector2(21, 0).rotate(self.ang))):
            self.desireDir += pg.Vector2(-1,0).rotate(self.ang) #.normalize()
            maxSpeed = 5
            wandrStr = .01
            steerStr = 5

        randDir = pg.Vector2(cos(radians(randAng)),sin(radians(randAng)))
        self.desireDir = pg.Vector2(self.desireDir + randDir * wandrStr).normalize()
        dzVel = self.desireDir * maxSpeed
        dzStrFrc = (dzVel - self.vel) * steerStr
        accel = dzStrFrc if pg.Vector2(dzStrFrc).magnitude() <= steerStr else pg.Vector2(dzStrFrc.normalize() * steerStr)
        velo = self.vel + accel * dt
        self.vel = velo if pg.Vector2(velo).magnitude() <= maxSpeed else pg.Vector2(velo.normalize() * maxSpeed)
        self.pos += self.vel * dt
        self.ang = degrees(atan2(self.vel[1],self.vel[0]))
        # adjusts angle of img to match heading
        self.image = pg.transform.rotate(self.orig_img, -self.ang)
        self.rect = self.image.get_rect(center=self.rect.center)  # recentering fix
        # actually update position
        self.rect.center = self.pos # ok, i dont know if we should implement that home is 0,0. Perhaps for the own ant, but that gets messy with different coords.

    def sensCheck(self, pos1, pos2): # checks given points in Array, IDs, and pixels on screen.
        sdpos1 = (int(pos1[0]/PRATIO),int(pos1[1]/PRATIO)) # scaled down points
        sdpos2 = (int(pos2[0]/PRATIO),int(pos2[1]/PRATIO))
        #sdpos1 = (int((pos1[0]/self.curW)*self.pgSize[0]), int((pos1[1]/self.curH)*self.pgSize[1]))
        #sdpos2 = (int((pos2[0]/self.curW)*self.pgSize[0]), int((pos2[1]/self.curH)*self.pgSize[1]))
        array_r1 = self.phero.img_array[sdpos1] # gives rgb value
        array_r2 = self.phero.img_array[sdpos2]
        array_result = (max(array_r1[0], array_r2[0]), max(array_r1[1], array_r2[1]), max(array_r1[2], array_r2[2])) # combines the two sensors into one.

        #is1ID = self.phero.pixelID[sdpos1] == self.antID
        is1ID = self.isMyTrail[sdpos1]
        #is2ID = self.phero.pixelID[sdpos2] == self.antID
        is2ID = self.isMyTrail[sdpos2]
        isID = is1ID or is2ID # what the hell

        ga_r1 = self.drawSurf.get_at(pos1)[:3]
        ga_r2 = self.drawSurf.get_at(pos2)[:3]
        ga_result = (max(ga_r1[0], ga_r2[0]), max(ga_r1[1], ga_r2[1]), max(ga_r1[2], ga_r2[2]))

        return array_result, isID, ga_result

class PheroGrid():
    def __init__(self, bigSize):
        self.surfSize = (int(bigSize[0]/PRATIO), int(bigSize[1]/PRATIO))
        self.image = pg.Surface(self.surfSize).convert() # stores into a more drawbale instance
        self.img_array = np.array(pg.surfarray.array3d(self.image),dtype=float)#.astype(np.float64)
        #self.pixelID = np.zeros(self.surfSize)
    def update(self, dt):
        self.img_array -= .1 * (60/FPS) * ((dt/10) * FPS) # Decay value
        self.img_array = self.img_array.clip(0,255) # ensures stays within range
        #self.pixelID[ (self.img_array == (0, 0, 0))[:, :, 0] ] = 0  # not sure if works, or worth it
        #indices = (img_array == (0, 0, 0))[:, :, 0] # alternative in 2 lines
        #pixelID[indices] = 0
        #self.img_array[self.img_array < 1] = 0  # ensure no leftover floats <1
        #self.img_array[self.img_array > 255] = 255  # ensures nothing over 255, replaced by clip
        pg.surfarray.blit_array(self.image, self.img_array) # draws the surface
        return self.image

class Food(pg.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos
        self.image = pg.Surface((16, 16)) # same as before
        self.image.fill(0)
        self.image.set_colorkey(0)
        pg.draw.circle(self.image, [2,150,2], [8, 8], 4) # draws the food circle
        self.rect = self.image.get_rect(center=pos) # dont know the point of this actually
    def pickup(self):
        self.kill() #.kill probably just deletes the sprite.

class Vec2(): # pointless class, we will just use numpy.
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y
	def vint(self):
		return (int(self.x), int(self.y))

def main():
    pg.init()  # prepare window
    pg.display.set_caption("NAnts") 
    try: pg.display.set_icon(pg.img.load("nants.png"))
    except: print("FYI: nants.png icon not found, skipping..")
    # house keeping stuff
    # setup fullscreen or window mode
    if FLLSCRN:  #screen = pg.display.set_mode((0,0), pg.FULLSCREEN)
        currentRez = (pg.display.Info().current_w, pg.display.Info().current_h)
        screen = pg.display.set_mode(currentRez, pg.SCALED | pg.NOFRAME | pg.FULLSCREEN, vsync=VSYNC)
    else: screen = pg.display.set_mode((WIDTH, HEIGHT), pg.SCALED, vsync=VSYNC)
    # some more housekeeping..

    cur_w, cur_h = screen.get_size()
    screenSize = (cur_w, cur_h)
    nest = (100, 300)

    #background = pg.img.load("background.png").convert_alpha()

    workers = pg.sprite.Group() # creates worker array
    pheroLayer = PheroGrid(screenSize)

    for n in range(ANTS):
        workers.add(Ant(screen, nest, pheroLayer)) # loops through to create the ants

    foodList = []
    foods = pg.sprite.Group() 
    clock = pg.time.Clock()
    fpsChecker = 0
    # main loop
    while True:
        for e in pg.event.get():
            if e.type == pg.QUIT or e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                return
            elif e.type == pg.MOUSEBUTTONDOWN:
                mousepos = pg.mouse.get_pos()
                if e.button == 1: # and pg.Vector2(mousepos).distance_to(nest) > 242:
                    foodBits = 200
                    fRadius = 50
                    for i in range(0, foodBits): # spawn food bits evenly within a circle
                        dist = pow(i / (foodBits - 1.0), 0.5) * fRadius
                        angle = 2 * pi * 0.618033 * i
                        fx = mousepos[0] + dist * cos(angle)
                        fy = mousepos[1] + dist * sin(angle)
                        foods.add(Food((fx,fy)))
                        # draws food
                    foodList.extend(foods.sprites()) # extends food list to include new sprites
                if e.button == 3: # deletes food that is right clicked on
                    for fbit in foodList:
                        if pg.Vector2(mousepos).distance_to(fbit.rect.center) < fRadius+5:
                            fbit.pickup()
                    foodList = foods.sprites()

        dt = clock.tick(FPS) / 100 # change in time is some function of FPS

        pheroImg = pheroLayer.update(dt) # updates phero

        workers.update(dt) # updates the ants

        screen.fill(0) # fill MUST be after sensors update, so previous draw is visible to them. VERY IMPORTANT!!

        rescaled_img = pg.transform.scale(pheroImg, (cur_w, cur_h)) # rescaled
        pg.Surface.blit(screen, rescaled_img, (0,0))

        foods.draw(screen)

        pg.draw.circle(screen, [40,10,10], (nest[0],nest[1]+6), 6, 3)
        pg.draw.circle(screen, [50,20,20], (nest[0],nest[1]+4), 9, 4)
        pg.draw.circle(screen, [60,30,30], (nest[0],nest[1]+2), 12, 4)
        pg.draw.circle(screen, [70,40,40], nest, 16, 5) # draws nest hole

        # pg.draw.rect(screen, (50,50,50), [900, 100, 50, 400]) # walls
        # pg.draw.rect(screen, (50,50,50), [1000, 200, 510, 40])
        # pg.draw.rect(screen, (50,50,50), [100, 210, 140, 400])
        # pg.draw.rect(screen, (50,50,50), [3000, 120, 1510, 20])

        workers.draw(screen)
        pg.display.update()

        # Outputs framerate once per second
        fpsChecker+=1  #fpsChecker = 0  # must go before main loop
        if fpsChecker>=FPS:  # quick debug to see fps in terminal
            print(round(clock.get_fps(),2)) #print((dt/10)*FPS)
            fpsChecker=0

if __name__ == '__main__':
    main() 
    pg.quit()