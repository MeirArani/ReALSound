import numpy as np
from realsound.core import FSM

MAX_LOST_FRAMES = 3


class Entity(FSM):
    def __init__(self):
        super().__init__(self)

        self.position = np.zeros((1, 2))
        self.velocity = np.zeros((1, 2))
        self.velocity_changed = np.array((False, False))

        self.active = False

        self.lost_frames = 0

    def update(self, new_corners):
        if new_corners is not None:

            if not self.active:
                self.active = True
                self.lost_frames = 0

            self.corners = new_corners

            new_position = (new_corners[0] + new_corners[3]) / 2
            new_velocity = new_position - self.position

            self.velocity_changed = (
                np.sign(new_velocity) != np.sign(self.velocity)
            ).squeeze()

            self.position = new_position
            self.velocity = new_velocity
            self.dimensions = new_corners[3] - new_corners[0]

            self.x = self.position[0]
            self.y = self.position[1]
            self.w = self.dimensions[0]
            self.h = self.dimensions[1]
        else:
            self.lost_frames += 1
            if self.lost_frames > MAX_LOST_FRAMES:
                self.active = False


class Paddle(Entity):
    def __init__(self):
        super().__init__()

        self.score = 0

    def update(self, new_corners):
        return super().update(new_corners)


class Ball(Entity):
    def __init__(self):
        super().__init__()

    def update(self, new_corners):
        return super().update(new_corners)
