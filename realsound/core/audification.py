from PySide6.QtCore import QObject


# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

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

from realsound.cv.NewPong import GameState

"""PySide6 port of the spatialaudio/audiopanning example from Qt v6.x"""


class AudioWidget(QObject):

    def __init__(self, parent):
        super().__init__(parent)
        self._file_dialog = None
        self.setMinimumSize(400, 300)

        form = QFormLayout()

        file_layout = QHBoxLayout()
        self._file_edit = QLineEdit()
        self._file_edit.setPlaceholderText("Audio File")
        file_layout.addWidget(self._file_edit)
        self._file_dialog_button = QPushButton("Choose...")
        file_layout.addWidget(self._file_dialog_button)
        form.addRow(file_layout)

        self._azimuth = QSlider(Qt.Orientation.Horizontal)
        self._azimuth.setRange(-180, 180)
        form.addRow("Azimuth (-180 - 180 degree):", self._azimuth)

        self._elevation = QSlider(Qt.Orientation.Horizontal)
        self._elevation.setRange(-90, 90)
        form.addRow("Elevation (-90 - 90 degree)", self._elevation)

        self._distance = QSlider(Qt.Orientation.Horizontal)
        self._distance.setRange(0, 1000)
        self._distance.setValue(100)
        form.addRow("Distance (0 - 10 meter):", self._distance)

        self._occlusion = QSlider(Qt.Orientation.Horizontal)
        self._occlusion.setRange(0, 400)
        form.addRow("Occlusion (0 - 4):", self._occlusion)

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

        self.main_layout = QGridLayout(self)

        self.main_layout.addLayout(form, 1, 0)
        self.main_layout.setRowStretch(0, 1)
        self.main_layout.setRowStretch(2, 1)

        self._mode = QComboBox()
        self._mode.addItem("Surround", QAudioEngine.Surround)
        self._mode.addItem("Stereo", QAudioEngine.Stereo)
        self._mode.addItem("Headphone", QAudioEngine.Headphone)

        form.addRow("Output mode:", self._mode)

        self._animate_button = QCheckBox("Animate sound position")
        form.addRow(self._animate_button)

        self._file_edit.textChanged.connect(self.file_changed)
        self._file_dialog_button.clicked.connect(self.open_file_dialog)

        self._azimuth.valueChanged.connect(self.update_position)
        self._elevation.valueChanged.connect(self.update_position)
        self._distance.valueChanged.connect(self.update_position)
        self._occlusion.valueChanged.connect(self.new_occlusion)

        self._room_dimension.valueChanged.connect(self.update_room)
        self._reverb_gain.valueChanged.connect(self.update_room)
        self._reflection_gain.valueChanged.connect(self.update_room)

        self._mode.currentIndexChanged.connect(self.mode_changed)

        self._engine = QAudioEngine()
        self._engine.setOutputMode(QAudioEngine.Headphone)
        self._room = QAudioRoom(self._engine)
        self._room.setWallMaterial(QAudioRoom.BackWall, QAudioRoom.BrickBare)
        self._room.setWallMaterial(QAudioRoom.FrontWall, QAudioRoom.BrickBare)
        self._room.setWallMaterial(QAudioRoom.LeftWall, QAudioRoom.BrickBare)
        self._room.setWallMaterial(QAudioRoom.RightWall, QAudioRoom.BrickBare)
        self._room.setWallMaterial(QAudioRoom.Floor, QAudioRoom.Marble)
        self._room.setWallMaterial(QAudioRoom.Ceiling, QAudioRoom.WoodCeiling)
        self.update_room()

        self._listener = QAudioListener(self._engine)
        self._listener.setPosition(QVector3D())
        self._listener.setRotation(QQuaternion())
        self._engine.start()

        # SOUNDS
        # BALL SOUND
        self.sound_ball_pos = QSpatialSound(self._engine)
        self.sound_ball_pos.setSource(
            QUrl.fromLocalFile(
                "C:\\Users\\cloud\\source\\repos\\ReALSound\\sounds\\ball440.wav"
            )
        )
        self.sound_ball_pos.setAutoPlay(False)
        self.sound_ball_pos.setSize(5)
        self.sound_ball_pos.setLoops(QSpatialSound.Infinite)

        # GOAL SOUND
        self.sound_goal = QSpatialSound(self._engine)
        self.sound_goal.setSource(
            QUrl.fromLocalFile(
                "C:\\Users\\cloud\\source\\repos\\ReALSound\\sounds\\goal.wav"
            )
        )
        self.sound_goal.setAutoPlay(False)
        self.sound_goal.setSize(5)
        self.sound_goal.setLoops(QSpatialSound.Once)
        self.sound_goal.setPosition(QVector3D())
        self.sound_goal.setRotation(QQuaternion())

        # HIT SOUND
        self.sound_hit = QSpatialSound(self._engine)
        self.sound_hit.setSource(
            QUrl.fromLocalFile(
                "C:\\Users\\cloud\\source\\repos\\ReALSound\\sounds\\hit.wav"
            )
        )
        self.sound_hit.setAutoPlay(False)
        self.sound_hit.setSize(5)
        self.sound_hit.setLoops(QSpatialSound.Once)
        self.sound_hit.setPosition(QVector3D())
        self.sound_hit.setRotation(QQuaternion())

        self.update_position()

        self._animation = QPropertyAnimation(self._azimuth, b"value")
        self._animation.setDuration(10000)
        self._animation.setStartValue(-180)
        self._animation.setEndValue(180)
        self._animation.setLoopCount(-1)
        self._animate_button.toggled.connect(self.animate_changed)

    @Slot(float, float)
    def update_ball_sound_position(self, dx, dy):
        self.update_sound_position(self.sound_ball_pos, dx, dy)

    def update_sound_position(self, sound, dx, dy):
        az = dx * math.pi - (math.pi / 2)
        el = self._elevation.value() / 180.0 * math.pi
        d = self._distance.value()

        x = d * math.sin(az) * math.cos(el)
        y = d * math.sin(el)
        z = -d * math.cos(az) * math.cos(el)
        sound.setPosition(QVector3D(x, y, z))

    @Slot(bool)
    def toggle_ball_sound(self, toggle):
        if toggle:
            print("TOGGLING BALL SFX ON!")
            self.sound_ball_pos.play()
        else:
            print("TOGGLING BALL SFX OFF!")
            self.sound_ball_pos.pause()
        pass

    @Slot(GameState)
    def play_goal(self, player):
        print("PLAYING GOAL SFX!")
        self.sound_goal.play()

    @Slot(bool)
    def play_hit(self, playerOneHit):
        # self.update_sound_position(self.sound_hit, dx, dy)
        self.sound_hit.play()
        pass

    def set_file(self, file):
        self._file_edit.setText(file)

    def update_position(self):
        az = self._azimuth.value() / 180.0 * math.pi
        el = self._elevation.value() / 180.0 * math.pi
        d = self._distance.value()

        x = d * math.sin(az) * math.cos(el)
        y = d * math.sin(el)
        z = -d * math.cos(az) * math.cos(el)
        self.sound_ball_pos.setPosition(QVector3D(x, y, z))

    @Slot()
    def new_occlusion(self):
        self.sound_ball_pos.setOcclusionIntensity(self._occlusion.value() / 100.0)

    @Slot()
    def mode_changed(self):
        self._engine.setOutputMode(self._mode.currentData())

    @Slot(str)
    def file_changed(self, file):
        self.sound_ball_pos.setSource(QUrl.fromLocalFile(file))
        self.sound_ball_pos.setSize(5)
        self.sound_ball_pos.setLoops(QSpatialSound.Infinite)

    @Slot()
    def open_file_dialog(self):
        if not self._file_dialog:
            directory = QStandardPaths.writableLocation(QStandardPaths.MusicLocation)
            self._file_dialog = QFileDialog(self, "Open Audio File", directory)
            self._file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
            mime_types = [
                "audio/mpeg",
                "audio/aac",
                "audio/x-ms-wma",
                "audio/x-flac+ogg",
                "audio/x-wav",
            ]
            self._file_dialog.setMimeTypeFilters(mime_types)
            self._file_dialog.selectMimeTypeFilter(mime_types[0])

        if self._file_dialog.exec() == QDialog.Accepted:
            self._file_edit.setText(self._file_dialog.selectedFiles()[0])

    @Slot()
    def update_room(self):
        d = self._room_dimension.value()
        self._room.setDimensions(QVector3D(d, d, 400))
        self._room.setReflectionGain(float(self._reflection_gain.value()) / 100)
        self._room.setReverbGain(float(self._reverb_gain.value()) / 100)

    @Slot()
    def animate_changed(self):
        if self._animate_button.isChecked():
            self._animation.start()
        else:
            self._animation.stop()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    name = "Spatial Audio Test Application"
    QCoreApplication.setApplicationVersion(qVersion())
    QGuiApplication.setApplicationDisplayName(name)

    argument_parser = ArgumentParser(
        description=name, formatter_class=RawTextHelpFormatter
    )
    argument_parser.add_argument("file", help="File", nargs="?", type=str)
    options = argument_parser.parse_args()

    w = AudioWidget()
    w.show()

    if options.file:
        w.set_file(options.file)

    sys.exit(app.exec())
