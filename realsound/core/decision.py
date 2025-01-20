import numpy as np
from realsound.cv import harris
from realsound.core import Ball, Paddle

HIT_DIST = 75


class DecisionLayer:

    def __init__(self):
        self.current_state = self.attract

        self.entities = {"p1": Paddle(), "p2": Paddle(), "ball": Ball()}

    def decide(self, new_corners, frame):
        for entity, corners in new_corners.items():
            self.entities[entity].update(corners)

        self.current_state = self.current_state()

        harris.add_text(frame, self.current_state.__name__, (290, 50))
        harris.add_text(
            frame,
            f"{self.p1.score} - {self.p2.score}",
            (290, 400),
        )

    # State logic
    def attract(self):
        return self.intermission if self.p1.active and self.p2.active else self.attract

    def intermission(self):  # Curse you break statement
        return self.match if self.ball.active else self.intermission

    def match(self):

        if self.ball.velocity_changed[0]:
            if dist(self.p1.position, self.ball.position) < HIT_DIST:
                print("P1 Hit!")
            elif dist(self.p2.position, self.ball.position) < HIT_DIST:
                print("P2 Hit!")
        elif self.ball.lost_frames > 1:
            if self.ball.x > self.p2.x:
                return self.goal(self.p1)
            elif self.ball.x < self.p1.x:
                return self.goal(self.p2)

        return self.match

    def goal(self, scorer):
        scorer.score += 1
        self.ball.active = False
        print(f"{self.p1.score} - {self.p2.score}")
        return self.intermission

    def win(self):
        print("WIN!")
        return self.attract

    def __getattr__(self, name):
        if name in ["p1", "p2", "ball"]:
            return self.entities[name]
        else:
            raise AttributeError

    def __setattr__(self, name, value):
        if name in ["p1", "p2", "ball"]:
            self.entities[name] = value
        else:
            super().__setattr__(name, value)


def dist(a, b):
    return np.linalg.norm(abs(a - b))
