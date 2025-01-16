import numpy as np
from realsound.core import FSM, State


class Entity(FSM):
    def __init__(self, corners):
        super().__init__(self)
        self.corners = corners
        self.position = (self.corners[0] + self.corners[2]) / 2


class EState(State):
    def __init__(self):
        super().__init__(self)


class Paddle(Entity):
    def __init__(self, corners):
        super().__init__(corners)


class Ball(Entity):
    def __init__(self, corners):
        super().__init__(corners)
