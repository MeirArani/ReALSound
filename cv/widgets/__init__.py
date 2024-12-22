import sys
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QSlider,
    QBoxLayout,
    QGridLayout,
    QLabel,
    QHBoxLayout,
)


class CVSlider(QHBoxLayout):

    def __init__(self, settings, parent=None):
        super(CVSlider, self).__init__(parent)

        self.label = QLabel(f"{settings["name"] or "_"}: {settings["value"]}")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(settings["min"] if "min" in settings else 100)
        self.slider.setMaximum(settings["max"])
        self.slider.singleStep = settings["step"] if "step" in settings else 1
        self.slider.value = (
            settings["value"] if "value" in settings else self.slider.value
        )
        self.slider.valueChanged.connect(self.on_move)

        self.addWidget(self.label)
        self.addWidget(self.slider)

    @Slot(int)
    def on_move(self, val):
        print("SOMETHING IS HAPPENING")
        self.label.setText(f"{self.label.text().split(":")[0]}: {val}")
