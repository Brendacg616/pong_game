#!/usr/bin/env python

import sys
import sdl2
import sdl2.ext

import rospy
from pong_game.msg import racket

WHITE = sdl2.ext.Color(255, 255, 255)
YELLOW = sdl2.ext.Color(255, 255, 0)

height = 600
width = 800

class SoftwareRenderer(sdl2.ext.SoftwareSpriteRenderSystem):
    def __init__(self, window):
        super(SoftwareRenderer, self).__init__(window)

    def render(self, components):
        sdl2.ext.fill(self.surface, sdl2.ext.Color(0, 0, 0))
        sdl2.ext.draw.line(self.surface, sdl2.ext.Color(255,255,255),(int(width/2), 0, int(width/2), height))
        super(SoftwareRenderer, self).render(components)

class MovementSystem(sdl2.ext.Applicator):
    def __init__(self, minx, miny, maxx, maxy):
        super(MovementSystem, self).__init__()
        self.componenttypes = Velocity, sdl2.ext.Sprite
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

    def process(self, world, componentsets):
        for velocity, sprite in componentsets:
            swidth, sheight = sprite.size
            sprite.x += velocity.vx
            sprite.y += velocity.vy

            sprite.x = max(self.minx, sprite.x)
            sprite.y = max(self.miny, sprite.y)

            pmaxx = sprite.x + swidth
            pmaxy = sprite.y + sheight
            if pmaxx > self.maxx:
                sprite.x = self.maxx - swidth
            if pmaxy > self.maxy:
                sprite.y = self.maxy - sheight


class Velocity(object):
    def __init__(self):
        super(Velocity, self).__init__()
        self.vx = 0
        self.vy = 0


class TrackingAIController(sdl2.ext.Applicator):
    def __init__(self, miny, maxy):
        super(TrackingAIController, self).__init__()
        self.componenttypes = PlayerData, Velocity, sdl2.ext.Sprite
        self.miny = miny
        self.maxy = maxy
        self.ball = None

    def process(self, world, componentsets):
        for pdata, vel, sprite in componentsets:
            if not pdata.ai:
                continue

            centery = sprite.y + sprite.size[1] // 2
            if self.ball.velocity.vx > 0:
                # ball is moving away from the AI
                if centery < self.maxy // 2:
                    vel.vy = 3
                elif centery > self.maxy // 2:
                    vel.vy = -3
                else:
                    vel.vy = 0
            else:
                bcentery = self.ball.sprite.y + self.ball.sprite.size[1] // 2
                if bcentery < centery:
                    vel.vy = -3
                elif bcentery > centery:
                    vel.vy = 3
                else:
                    vel.vy = 0


class PlayerData(object):
    def __init__(self):
        super(PlayerData, self).__init__()
        self.ai = False
        self.score = 0


class Player(sdl2.ext.Entity):
    def __init__(self, world, sprite, posx=0, posy=0, ai=False):
        self.sprite = sprite
        self.sprite.position = posx, posy
        self.velocity = Velocity()
        self.playerdata = PlayerData()
        self.playerdata.ai = ai


class Ball(sdl2.ext.Entity):
    def __init__(self, world, sprite, posx=0, posy=0):
        self.sprite = sprite
        self.sprite.position = posx, posy
        self.velocity = Velocity()

class CollisionSystem(sdl2.ext.Applicator):
    def __init__(self, minx, miny, maxx, maxy):
        super(CollisionSystem, self).__init__()
        self.componenttypes = Velocity, sdl2.ext.Sprite
        self.ball = None
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.score_left = 0
        self.score_right = 0

    def _overlap(self, item):
        pos, sprite = item
        if sprite == self.ball.sprite:
            return False

        left, top, right, bottom = sprite.area
        bleft, btop, bright, bbottom = self.ball.sprite.area

        return (bleft < right and bright > left and
                btop < bottom and bbottom > top)

    def process(self, world, componentsets):
        collitems = [comp for comp in componentsets if self._overlap(comp)]
        if collitems:
            self.ball.velocity.vx = -self.ball.velocity.vx
            sprite = collitems[0][1]
            ballcentery = self.ball.sprite.y + self.ball.sprite.size[1] // 2
            halfheight = sprite.size[1] // 2
            stepsize = halfheight // 10
            degrees = 0.7
            paddlecentery = sprite.y + halfheight
            if ballcentery < paddlecentery:
                factor = (paddlecentery - ballcentery) // stepsize
                self.ball.velocity.vy = -int(round(factor * degrees))
            elif ballcentery > paddlecentery:
                factor = (ballcentery - paddlecentery) // stepsize
                self.ball.velocity.vy = int(round(factor * degrees))
            else:
                self.ball.velocity.vy = - self.ball.velocity.vy
        if (self.ball.sprite.y <= self.miny or
            self.ball.sprite.y + self.ball.sprite.size[1] >= self.maxy):
            self.ball.velocity.vy = - self.ball.velocity.vy

        # Increase score if 
        if (self.ball.sprite.x <= self.minx):
            self.score_right = self.score_right+ 1

        if (self.ball.sprite.x + self.ball.sprite.size[0] >= self.maxx):
            self.score_left = self.score_left + 1

        if (self.ball.sprite.x <= self.minx or
            self.ball.sprite.x + self.ball.sprite.size[0] >= self.maxx):
            self.ball.velocity.vx = - self.ball.velocity.vx
            self.ball.sprite.x = int(self.maxx / 2)
            self.ball.sprite.y = int(self.maxy / 2)
            
            rospy.loginfo("SCORE: Computer %s - Player %s", self.score_left, self.score_right)

class Game(object):
    def __init__(self):
        sdl2.ext.init()
        self.window = sdl2.ext.Window("The Pong Game", size=(width, height))
        self.window.show()

        self.world = sdl2.ext.World()

        spriterenderer = SoftwareRenderer(self.window)

        factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
        sp_paddle1 = factory.from_color(WHITE, size=(20, 100))
        sp_paddle2 = factory.from_color(WHITE, size=(20, 100))

        self.sp_ball = factory.from_color(YELLOW, size=(20, 20))

        movement = MovementSystem(0, 0, 800, 600)
        self.collision = CollisionSystem(0, 0, 800, 600)
        spriterenderer = SoftwareRenderer(self.window)
        self.aicontroller = TrackingAIController(0, 600)

        self.world.add_system(self.aicontroller)
        self.world.add_system(movement)
        self.world.add_system(self.collision)
        self.world.add_system(spriterenderer)

        self.player_right = Player(self.world, sp_paddle1, 780, 250)
        self.player_left = Player(self.world, sp_paddle2, 0, 250, True)


        ball = Ball(self.world, self.sp_ball, 390, 290)
        ball.velocity.vx = -5
        self.collision.ball = ball

        self.aicontroller.ball = ball
            

    def loop(self):
        self.world.process()


    def callback(self,msg):
        self.player_right.sprite.y = int (msg.position * 500 - 50)
        

player1 = None
def run():
    rospy.init_node('game_field', anonymous=True)
    game = Game()
    rospy.Subscriber("gamecontrol", racket, game.callback)
    rate = rospy.Rate(50)

    while not rospy.is_shutdown():
        game.loop()
        rate.sleep()
        

if __name__ == "__main__":
    run()