from enum import Enum
from importlib import resources
import math
import numpy as np
from realsound.core import FSM
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtSpatialAudio import QSpatialSound
from realsound.core.audification import AudioObject
from realsound.resources import config, sounds
import json
from PySide6.QtGui import QVector3D, QQuaternion
import time

MAX_LOST_FRAMES = 5
VELOCITY_MAX = 100
VELOCITY_MOE = 0.25

configs = json.loads(resources.read_text(config, "base.json"))["decision"]["entities"]


class Entity(QObject):

    def __init__(self, name, parent):
        super().__init__(parent)

        # Set up audio objects from config
        self.audio_objects = {}

        for obj_name, config in configs[name]["audio_objects"].items():

            sound = QSpatialSound(parent.client.audification._engine)
            sound.setSource(
                QUrl.fromLocalFile(resources.files(sounds).joinpath(config["path"]))
            )

            if config.get("loop", False):
                sound.setLoops(QSpatialSound.Loops.Infinite)
            sound.setAutoPlay(False)
            sound.setSize(5)
            sound.setPosition(QVector3D())
            sound.setRotation(QQuaternion())

            self.audio_objects[obj_name] = AudioObject(self, sound)

        self.name = name
        self.position = np.zeros((1, 2))
        self.velocity = np.zeros((1, 2))

        self.velocity_changed = np.array((False, False))
        self.moving = False
        self.active = False

        self.lost_frames = 0

    def update(self, new_corners):
        if new_corners is not None:
            new_position = (new_corners[0] + new_corners[3]) / 2

            # Special Case when spawning or first discovered
            # No velocity or other similar data this frame
            if not self.active:
                self.activate()
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

                    # If we're moving this frame
                    self.moving = np.any(abs(new_velocity) > VELOCITY_MOE)

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
            self.deactivate()

    def activate(self):
        self.active = True
        self.velocity = np.zeros((2))
        self.velocity_changed = np.full((2), False)

    def deactivate(self):
        self.active = False
        self.moving = False


class Paddle(Entity):

    MIN_BEEP_SPEED = 0.75
    MAX_BEEP_SPEED = 0.05
    on_hit = Signal(str)

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.score = 0
        self.last_beep = time.time()
        self.beep_speed = Paddle.MIN_BEEP_SPEED

    def update(self, new_corners):
        super().update(new_corners)
        if self.active and self.parent().current_state == self.parent().match:
            now = time.time()
            if now - self.last_beep > self.beep_speed:
                self.beep()

    def beep(self):
        if self.name == "p1":
            self.audio_objects["move"].play()
            self.last_beep = time.time()

    def hit(self):
        self.on_hit.emit(self.name)
        self.audio_objects["hit"].play()

    def goal(self):
        print("Playing Goal SFX")
        self.audio_objects["goal"].play()

    def win(self):
        print("Playing Win SFX")
        self.audio_objects["win"].play()

    class Pitch(Enum):
        LOWEST = 1
        LOW = 2
        GOOD = 3
        HIGH = 4
        HIGHEST = 5


class Ball(Entity):

    on_ricochet = Signal()

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def update(self, new_corners):
        super().update(new_corners)
        az_left = -((self.x - 100) * math.pi / 1000)
        az_right = (self.x - 100) * math.pi / 1000
        self.audio_objects["move_l"].set_position(az=az_left)
        self.audio_objects["move_r"].set_position(az=az_right)

    def ricochet(self):
        self.on_ricochet.emit()
        self.audio_objects["bounce"].play()

    def activate(self):
        super().activate()
        # self.audio_objects["move_l"].play()
        # self.audio_objects["move_r"].play()

    def deactivate(self):
        super().deactivate()
        # self.audio_objects["move_l"].stop()
        # self.audio_objects["move_r"].stop()
