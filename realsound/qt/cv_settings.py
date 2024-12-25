from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListView
import json
from importlib import resources
from realsound import config
from PySide6.QtWidgets import QDialog, QVBoxLayout, QGridLayout
from .cv_slider import CVSliderWidget


class CVSettingsListWidget(QDialog):
    def __init__(self, config_name=None, parent=None):
        super().__init__(parent)
        self.settings = json.loads(
            resources.read_text(config, config_name)
        ) or json.loads(resources.read_text(config, "cv_settings.json").read_text())

        self.cv_settings = QVBoxLayout()

        for control, settings in self.settings.items():
            slider = CVSliderWidget(settings)
            slider.slider.valueChanged.connect(
                lambda value, name=control: self.update_settings(name, value)
            )
            self.cv_settings.addLayout(slider)

        main_layout = QGridLayout(self)
        main_layout.addLayout(self.cv_settings, 0, 0)

    def update_settings(self, control, value):
        print(f"{control}: {value}")
        pass
