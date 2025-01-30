from enum import IntEnum
from importlib import resources
import math
from turtle import width
import numpy as np
from realsound.core import FSM
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtSpatialAudio import QSpatialSound
from realsound.core.audification import AudioObject, Pan
from realsound.core.decision import dist
from realsound.core.client import safe_ratio
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

        self.name = name
        self.client = parent.parent()

        # Set up audio objects from config
        self.audio_objects = {}
        self.load_audio_objects()

        self.position = np.zeros((1, 2))
        self.velocity = np.zeros((1, 2))

        self.velocity_changed = np.array((False, False))
        self.moving = False
        self.active = False

        self.lost_frames = 0

    def load_audio_objects(self):
        for obj_name, config in configs[self.name]["audio_objects"].items():
            sound = QSpatialSound(self.client.audification._engine)
            obj = AudioObject(self, sound)

            if config.get("paths", False):
                for path in config["paths"].values():
                    obj._paths.append(
                        QUrl.fromLocalFile(resources.files(sounds).joinpath(path))
                    )
            else:
                obj._paths.append(
                    QUrl.fromLocalFile(resources.files(sounds).joinpath(config["path"]))
                )

            sound.setSource(obj._paths[0])

            if config.get("loop", False):
                sound.setLoops(QSpatialSound.Loops.Infinite)
            sound.setAutoPlay(False)
            sound.setSize(5)
            sound.setPosition(QVector3D())
            sound.setRotation(QQuaternion())

            self.audio_objects[obj_name] = obj

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
            self.top = new_corners[0][1]
            self.bottom = new_corners[1][1]

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

    on_hit = Signal(str)

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.score = 0
        for obj in self.audio_objects.values():
            obj.set_pan(Pan.LEFT) if self.name == "p1" else obj.set_pan(Pan.RIGHT)

    def update(self, new_corners):
        super().update(new_corners)

    def hit(self):
        self.on_hit.emit(self.name)
        self.audio_objects["hit"].play()

    def goal(self):
        print("Playing Goal SFX")
        self.audio_objects["goal"].play()

    def win(self):
        print("Playing Win SFX")
        self.audio_objects["win"].play()


class Ball(Entity):

    MIN_BEEP_SPEED = 0.2
    MAX_BEEP_SPEED = 0.05
    on_ricochet = Signal()

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.last_beep = time.time()
        self.beep_speed = Ball.MIN_BEEP_SPEED
        self.pitch = Pitch.GOOD

    def update(self, new_corners):
        super().update(new_corners)

        if self.parent().current_state == self.parent().match:
            # Find new beep speed
            self.beep_speed = calc_speed(
                self.parent().p1, self, self.client.frame_width
            )
            print(self.beep_speed)
            # Update pitch value
            pitch = calc_pitch(self.parent().p1, self, self.client.frame_height)
            if pitch != self.pitch:
                self.pitch = pitch
                self.audio_objects["move"].switch_sound(pitch)

            # Update panning
            self.audio_objects["move"].update_panning(self.x)
            # Check for beep
            now = time.time()
            if now - self.last_beep > self.beep_speed:
                self.beep()

    def beep(self):
        self.audio_objects["move"].play()
        self.last_beep = time.time()

    def ricochet(self):
        self.on_ricochet.emit()
        self.audio_objects["bounce"].play()

    def activate(self):
        super().activate()
        self.beep()

    def deactivate(self):
        super().deactivate()
        self.audio_objects["move"].stop()

    def set_pitch(self, Pitch):
        self.audio_objects["move"].switch_sound(Pitch)


def calc_speed(paddle, ball, width):
    dx = dist(paddle.x, ball.x)
    return min(
        abs(
            Ball.MAX_BEEP_SPEED
            + safe_ratio(ball.x, width) * (Ball.MIN_BEEP_SPEED - Ball.MAX_BEEP_SPEED)
        ),
        Ball.MIN_BEEP_SPEED,
    )


def calc_pitch(paddle, ball, height):
    if paddle.top <= ball.y <= paddle.bottom:
        return Pitch.GOOD
    dy = ball.y - paddle.y
    if dy < 0:
        return Pitch.HIGH if dy < paddle.top / 2 else Pitch.HIGHEST
    elif dy > 0:
        return Pitch.LOW if dy < (height - paddle.bottom) / 2 else Pitch.LOWEST


class Pitch(IntEnum):
    LOWEST = 0
    LOW = 1
    GOOD = 2
    HIGH = 3
    HIGHEST = 4
