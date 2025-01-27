import numpy as np
from realsound.core import Ball, Paddle
from PySide6.QtCore import QObject

HIT_DIST = 75
WALL_DIST = 30
GOAL_BUFFER = 5
WIN_SCORE = 11


class DecisionLayer(QObject):

    def __init__(self, parent):
        super().__init__(parent)
        self.current_state = self.attract
        self.entities = {
            "p1": Paddle("p1", self),
            "p2": Paddle("p2", self),
            "ball": Ball("ball", self),
        }

    def decide(self, new_corners):
        for entity, corners in new_corners.items():
            self.entities[entity].update(corners)

        self.current_state = self.current_state()

    # State logic
    def attract(self):
        if self.p1.active and self.p2.active:
            self.ball.active = False
            return self.intermission
        else:
            return self.attract

    def intermission(self):
        return self.match if self.ball.active else self.intermission

    def match(self):
        # If the ball's X velocity changes
        # There must have been a hit
        if self.ball.velocity_changed[0]:
            if dist(self.p1.position, self.ball.position) < HIT_DIST:
                self.p1.hit()
            elif dist(self.p2.position, self.ball.position) < HIT_DIST:
                self.p2.hit()

        # If the ball's Y velocity changes
        # There might have been a ricochet
        # If it bounced off a top/bottom wall
        elif self.ball.velocity_changed[1]:
            if (
                self.ball.y < WALL_DIST
                or self.parent().frame.shape[0] - self.ball.y < WALL_DIST
            ):
                self.ball.ricochet()

        # If the ball goes missing long enough
        # There must have been a goal
        if not self.ball.active:
            if self.ball.x + GOAL_BUFFER > self.p2.x:
                return self.goal(self.p1)
            elif self.ball.x + GOAL_BUFFER < self.p1.x:
                return self.goal(self.p2)

        # If the paddles go missing long enough
        # AND the ball is on a certain side of the screen
        # The other player has won
        if not (self.p1.active and self.p2.active):
            if self.ball.x > (self.parent().frame.shape[1] // 2):
                return self.win(self.p1)
            else:
                return self.win(self.p2)

        return self.match

    def goal(self, scorer):
        scorer.score += 1
        print(f"{self.p1.score} - {self.p2.score}")
        return self.intermission

    def win(self, winner):
        winner.score += 1
        print(f"{winner} WINS!")
        return self.attract

    def __getattr__(self, name):
        if name in ["p1", "p2", "ball"]:
            return self.entities[name]
        elif name == "state":
            return self.current_state.__name__
        else:
            raise AttributeError

    def __setattr__(self, name, value):
        if name in ["p1", "p2", "ball"]:
            self.entities[name] = value
        else:
            super().__setattr__(name, value)


def dist(a, b):
    return np.linalg.norm(abs(a - b))
