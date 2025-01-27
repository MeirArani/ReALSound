import numpy as np
from realsound.core import FSM
from PySide6.QtCore import QObject, Signal

MAX_LOST_FRAMES = 5
VELOCITY_MAX = 100
VELOCITY_MOE = 0.25


class Entity(QObject):

    def __init__(self, name, parent):
        super().__init__(parent)
        self.name = name
        self.position = np.zeros((1, 2))
        self.velocity = np.zeros((1, 2))
        self.velocity_changed = np.array((False, False))

        self.active = False

        self.lost_frames = 0

    def update(self, new_corners):
        if new_corners is not None:
            new_position = (new_corners[0] + new_corners[3]) / 2

            # Special Case when spawning or first discovered
            # No velocity or other similar data this frame
            if not self.active:
                self.active = True
                self.velocity = np.zeros((2))
                self.velocity_changed = np.full((2), False)
            else:
                new_velocity = new_position - self.position

                # If new velocity isn't impossible
                # i.e., an incorrect object across the screen
                # was accidentally flagged as this entity
                if np.any(abs(new_velocity) > VELOCITY_MAX):
                    self.lost_frame()
                    return

                # If new and old velocity aren't zeros
                if np.any(new_velocity) and np.any(self.velocity):
                    # If the velocity changed signs
                    # And is beyond a basic MOE
                    self.velocity_changed = (
                        (np.sign(new_velocity) != np.sign(self.velocity))
                        & (abs(new_velocity) > VELOCITY_MOE)
                    ).squeeze()
                else:  # if Zeros, treat like no velocity change
                    self.velocity_changed = np.full((2), False)

                self.velocity = new_velocity

            self.corners = new_corners
            self.position = new_position
            self.dimensions = new_corners[3] - new_corners[0]
            self.x = self.position[0]
            self.y = self.position[1]
            self.w = self.dimensions[0]
            self.h = self.dimensions[1]
            self.lost_frames = 0
        else:
            self.lost_frame()

    def lost_frame(self):
        self.lost_frames += 1
        self.velocity_changed = np.full((2), False)
        if self.lost_frames > MAX_LOST_FRAMES:
            self.active = False


class Paddle(Entity):

    on_hit = Signal(str)

    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.score = 0

    def update(self, new_corners):
        return super().update(new_corners)

    def hit(self):
        self.on_hit.emit(self.name)


class Ball(Entity):

    on_ricochet = Signal()

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def update(self, new_corners):
        return super().update(new_corners)

    def ricochet(self):
        self.on_ricochet.emit()
