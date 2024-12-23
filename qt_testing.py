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
from cv.widgets import CVSlider


class CVControls(QDialog):

    def __init__(self, parent=None):
        super(CVControls, self).__init__(parent)

        self.setWindowTitle("CV Controls")

        self.control_settings = {
            "thresh": {
                "name": "threshold",
                "min": 0,
                "max": 100,
                "value": 2,
                "name": "threshold",
                "tick": 20,
            },
            "block": {"name": "blocksize", "min": 1, "max": 5, "value": 2},
            "k_size": {"name": "k_size", "min": 1, "max": 4, "value": 3},
            "k": {"name": "k", "min": 3, "max": 6, "value": 4},
            "points": {
                "name": "Number of Points",
                "min": 1,
                "max": 25,
                "value": 12,
                "tick": 5,
            },
            "distance": {
                "name": "Minimum Distance",
                "min": 1,
                "max": 20,
                "value": 3,
                "tick": 5,
            },
        }

        self.controls = {}

        for control, settings in self.control_settings.items():
            self.controls.update({settings["name"]: CVSlider(settings)})

        self.cv_controls = QVBoxLayout()
        for control, cv_slider in self.controls.items():
            self.cv_controls.addLayout(cv_slider)

        main_layout = QGridLayout(self)
        main_layout.addLayout(self.cv_controls, 0, 0)


if __name__ == "__main__":
    # Create Qt app
    app = QApplication(sys.argv)
    # create and show the form
    form = CVControls()
    form.show()
    # run the main loop
    sys.exit(app.exec())
