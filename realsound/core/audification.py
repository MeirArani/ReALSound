from __future__ import annotations
import copy
from re import L
from tkinter import LEFT
from PySide6.QtCore import QObject

import math
import sys
from argparse import ArgumentParser, RawTextHelpFormatter

from PySide6.QtSpatialAudio import (
    QAudioRoom,
    QAudioEngine,
    QAudioListener,
    QSpatialSound,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QSlider,
    QWidget,
)
from PySide6.QtGui import QGuiApplication, QVector3D, QQuaternion
from PySide6.QtCore import (
    QCoreApplication,
    QPropertyAnimation,
    QStandardPaths,
    QUrl,
    Qt,
    qVersion,
    Slot,
)

from enum import IntEnum

"""PySide6 port of the spatial audio/audio panning example from Qt v6.x"""


class AudificationLayer(QObject):

    def __init__(self, parent):
        super().__init__(parent)
        self.client = parent
        self._azimuth = 0
        self._elevation = 0
        self._distance = 0
        self._room_dimension = 1000
        self._reverb_gain = 0
        self._reflection_gain = 0

        self._engine = QAudioEngine(self)
        self._engine.setOutputMode(QAudioEngine.Headphone)
        self._room = QAudioRoom(self._engine)
        self._room.setWallMaterial(QAudioRoom.BackWall, QAudioRoom.Transparent)
        self._room.setWallMaterial(QAudioRoom.FrontWall, QAudioRoom.Transparent)
        self._room.setWallMaterial(QAudioRoom.LeftWall, QAudioRoom.Transparent)
        self._room.setWallMaterial(QAudioRoom.RightWall, QAudioRoom.Transparent)
        self._room.setWallMaterial(QAudioRoom.Floor, QAudioRoom.Transparent)
        self._room.setWallMaterial(QAudioRoom.Ceiling, QAudioRoom.Transparent)
        self.update_room()

        self._listener = QAudioListener(self._engine)
        self._listener.setPosition(QVector3D())
        self._listener.setRotation(QQuaternion())

        self._engine.start()

    @Slot()
    def update_position(self):
        az = 0 / 180.0 * math.pi
        el = 0 / 180.0 * math.pi
        d = 100

        x = d * math.sin(az) * math.cos(el)
        y = d * math.sin(el)
        z = -d * math.cos(az) * math.cos(el)
        self.sound_ball_pos.setPosition(QVector3D(x, y, z))

    @Slot()
    def update_room(self):
        self._room.setDimensions(
            QVector3D(self._room_dimension, self._room_dimension, 400)
        )
        self._room.setReflectionGain(float(self._reflection_gain) / 100)
        self._room.setReverbGain(float(self._reverb_gain) / 100)

    @Slot(int)
    def update_room_dimension(self, size):
        self._room_dimension = size
        self.update_room()

    @Slot(int)
    def update_reverb_gain(self, amount):
        self._reverb_gain = amount
        self.update_room()

    @Slot(int)
    def update_reflection_gain(self, amount):
        self._reflection_gain = amount
        self.update_room()


class AudioObject(QObject):
    def __init__(self, parent, sound=None):
        super().__init__(parent)
        self.client = parent.parent().parent()

        self._azimuth = 0
        self._elevation = 0
        self._distance = 8000
        self._occlusion = 0

        self._paths = []

        self._sound = sound
        self._sound.setDirectivity(1)
        self._sound.setDirectivityOrder(100000000000000)
        self._sound.setSize(1)

    def set_pan(self, pan):
        if pan is Pan.LEFT:
            self.set_position(az=-math.pi / 2)
        elif pan is Pan.RIGHT:
            self.set_position(az=math.pi / 2)
        elif pan is Pan.CENTER:
            self.set_position(az=0)

    def update_panning(self, dx):
        from realsound.core.client import safe_ratio

        az = safe_ratio(dx, self.client.frame_width) * math.pi - math.pi / 2
        self.set_position(az=az)

    def set_position(self, az=0, el=0, dist=100):
        x = dist * math.sin(az) * math.cos(el)
        y = dist * math.sin(el)
        z = -dist * math.cos(az) * math.cos(el)
        self._sound.setPosition(QVector3D(x, y, z))
        self._sound.setRotation(
            QQuaternion.fromDirection(self._sound.position(), QVector3D(0, 1, 0))
        )

    def set_position_simple(self, dx, dy):
        az = (dx / 720) * math.pi - (math.pi / 2)
        el = self._elevation / 180.0 * math.pi
        el = 0
        d = self._distance

        x = d * math.sin(az) * math.cos(el)
        y = d * math.sin(el)
        z = -d * math.cos(az) * math.cos(el)
        self._sound.setPosition(QVector3D(x, y, z))
        self._sound.setRotation(QQuaternion(1, 0, 1 / 2 - dx / 720, 0))

    def set_position_adjusted(self, dx, dy):
        az = -((dx - 100) * math.pi / 1000)
        el = self._elevation / 180.0 * math.pi
        el = 0
        d = self._distance
        print(math.degrees(az))

        x = d * math.sin(az) * math.cos(el)
        y = d * math.sin(el)
        z = -d * math.cos(az) * math.cos(el)
        self._sound.setPosition(QVector3D(x, y, z))
        # self._sound.setRotation(QQuaternion(1, 0, 1, 0))

    def play(self):
        self._sound.play()

    def pause(self):
        self._sound.pause()

    def stop(self):
        self._sound.stop()

    def switch_sound(self, index):
        self._sound.setSource(self._paths[index])


class AudioWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        form = QFormLayout()
        file_layout = QHBoxLayout()

        self._room_dimension = QSlider(Qt.Orientation.Horizontal)
        self._room_dimension.setRange(0, 10000)
        self._room_dimension.setValue(1000)
        form.addRow("Room dimension (0 - 100 meter):", self._room_dimension)

        self._reverb_gain = QSlider(Qt.Orientation.Horizontal)
        self._reverb_gain.setRange(0, 500)
        self._reverb_gain.setValue(0)
        form.addRow("Reverb gain (0-5):", self._reverb_gain)

        self._reflection_gain = QSlider(Qt.Orientation.Horizontal)
        self._reflection_gain.setRange(0, 500)
        self._reflection_gain.setValue(0)
        form.addRow("Reflection gain (0-5):", self._reflection_gain)

        self._room_dimension.valueChanged.connect(parent.update_room_dimension)
        self._reverb_gain.valueChanged.connect(parent.update_reverb_gain)
        self._reflection_gain.valueChanged.connect(parent.update_reflection_gain)

        self.main_layout = QGridLayout(self)
        self.main_layout.addLayout(form, 1, 0)
        self.main_layout.setRowStretch(0, 1)
        self.main_layout.setRowStretch(2, 1)


class Pan(IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


if __name__ == "__main__":

    app = QApplication(sys.argv)

    name = "Spatial Audio Test Application"
    QCoreApplication.setApplicationVersion(qVersion())
    QGuiApplication.setApplicationDisplayName(name)

    w = AudioWidget(None)
    w.show()
    sys.exit(app.exec())
