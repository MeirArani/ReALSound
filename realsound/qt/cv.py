from PySide6 import QtCore
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QWidget,
    QSlider,
    QGridLayout,
    QLabel,
    QHBoxLayout,
)


import json
from importlib import resources
from realsound.resources import config
from PySide6.QtWidgets import QDialog, QVBoxLayout, QGridLayout

import numpy as np


class CVSettingsListWidget(QDialog):
    def __init__(self, default_config="base.json", parent=None):
        super().__init__(parent)

        # Load options
        self.defaults = json.loads(
            resources.read_text(config, default_config)
        ) or json.loads(resources.read_text(resources, "base.json").read_text())

        self.settings = {}

        self.settings_label = QLabel("CV Settings", self)

        self.main_layout = QGridLayout(self)

        self.main_layout.addWidget(self.settings_label, 1, 1)

        for i, (control, settings) in enumerate(self.defaults["vision"]["cv"].items()):
            slider = CVSliderWidget(settings)
            self.settings[control] = slider
            slider.slider.valueChanged.connect(
                lambda value, name=control: self.update_settings(name, value)
            )
            self.main_layout.addWidget(slider, i + 2, 1)

        self.main_layout.setRowStretch(0, 1)
        self.main_layout.setRowStretch(len(settings) + 3, 1)

        self.main_layout.setColumnStretch(1, 1)

    def update_settings(self, control, value):
        self.settings[control].slider.value = value
        pass


class CVSliderWidget(QWidget):

    moved = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.main_layout = QGridLayout(self)
        self.label = QLabel(f"{settings["name"] or "_"}: {settings["value"]}")
        self.label.setScaledContents(True)

        # self.label.setContentsMargins(QMargins(10, 10, 10, 10))

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.value = (
            settings["value"] if "value" in settings else self.slider.value
        )

        self.slider.setMinimum(settings["min"] if "min" in settings else 100)
        self.slider.setMaximum(settings["max"])

        self.slider.setSingleStep(settings["step"] if "step" in settings else 1)
        self.slider.setTickInterval(settings["tick"] if "tick" in settings else 1)
        self.slider.setTickPosition(QSlider.TickPosition.TicksAbove)

        self.slider.valueChanged.connect(self.on_move)

        self.main_layout.addWidget(self.label, 0, 0)
        self.main_layout.addWidget(self.slider, 0, 2)

        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnMinimumWidth(1, 10)
        self.main_layout.setColumnStretch(1, 0)
        self.main_layout.setColumnStretch(2, 1)

    @Slot(int)
    def on_move(self, val):
        self.label.setText(f"{self.label.text().split(":")[0]}: {val}")


class CVStatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)

        self.title_label = QLabel("CV Stats")
        self.paddle_l_label = QLabel("Left Paddle")
        self.paddle_r_label = QLabel("Right Paddle")
        self.ball_label = QLabel("Ball")
        self.state_label = QLabel("State")

        self.paddle_l_pos = QLabel("(0, 0)")
        self.paddle_r_pos = QLabel("(0, 0)")
        self.ball_pos = QLabel("(0, 0)")
        self.state_info = QLabel("ATTRACT")

        self.layout.addWidget(self.title_label, 1, 0, 1, 2)
        self.layout.addWidget(self.paddle_l_label, 2, 0)
        self.layout.addWidget(self.paddle_r_label, 3, 0)
        self.layout.addWidget(self.ball_label, 4, 0)
        self.layout.addWidget(self.state_label, 5, 0)

        self.layout.addWidget(self.paddle_l_pos, 2, 1)
        self.layout.addWidget(self.paddle_r_pos, 3, 1)
        self.layout.addWidget(self.ball_pos, 4, 1)
        self.layout.addWidget(self.state_info, 5, 1)

        self.layout.setRowStretch(6, 1)
        self.layout.setColumnMinimumWidth(0, 100)
        self.layout.setColumnMinimumWidth(1, 100)

    @Slot(np.ndarray, int)
    def update_stats(self, centers, state):
        self.paddle_l_pos.setText(f"({centers[0][0]}, {centers[0][1]})")
        self.paddle_r_pos.setText(f"({centers[1][0]}, {centers[1][1]})")
        self.ball_pos.setText(f"({centers[2][0]}, {centers[2][1]})")
        # self.state_info.setText(f"{GameState(state).name}")
