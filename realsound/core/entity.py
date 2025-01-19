import numpy as np
from realsound.core import FSM


class Entity(FSM):
    def __init__(self, corners):
        super().__init__(self)
        self.corners = corners
        self.position = (corners[0] + corners[2]) / 2
        self.dimensions = (corners[3] - corners[0]) / 2


class Paddle(Entity):
    def __init__(self, corners):
        super().__init__(corners)


class Ball(Entity):
    def __init__(self, corners):
        super().__init__(corners)
