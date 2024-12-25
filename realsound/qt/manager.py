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

from realsound.qt import CVSliderWidget


class CVControls(QDialog):

    def __init__(self, parent=None):
        super(CVControls, self).__init__(parent)

        self.setWindowTitle("CV Controls")

        for control, settings in self.control_settings.items():
            self.controls.update({settings["name"]: CVSliderWidget(settings)})

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
