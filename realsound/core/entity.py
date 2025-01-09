import numpy as np
from realsound.core import FSM


class Entity(FSM):
    def __init__(self):
        super().__init__(self)
        self.position = np.zeros(2, 1)


class Paddle(Entity):
    def __init__(self):
        super().__init__(self)


class Ball(Entity):
    def __init__(self):
        super().__init__()
