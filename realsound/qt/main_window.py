import sys
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import (
    QCapturableWindow,
    QMediaCaptureSession,
    QScreenCapture,
    QVideoFrame,
    QWindowCapture,
)
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QListView,
    QMessageBox,
    QPushButton,
    QWidget,
    QApplication,
)
from PySide6.QtCore import QCoreApplication, Slot

from realsound.qt.cv_settings import CVSettingsListWidget

from realsound.qt.window import ScreenCapturePreview

import numpy as np

import cv2 as cv

import tracemalloc


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame_counter = 0
        self.settings_label = QLabel("CV Settings", self)
        self.stats_label = QLabel("Stats", self)
        self.settings = CVSettingsListWidget(default_config="cv_settings.json")
        self.screen_cap = ScreenCapturePreview()
        self.screen_cap.frame_updated.connect(self.get_new_frame)

        self.test_button = QPushButton()
        self.test_button.clicked.connect(stop_trace)

        self.main_layout = QGridLayout(self)
        self.main_layout.addWidget(self.settings_label, 0, 0)
        self.main_layout.addWidget(self.settings, 1, 0, 2, 1)
        self.main_layout.addWidget(self.stats_label, 3, 0)
        self.main_layout.addWidget(self.test_button, 4, 0)
        self.main_layout.addWidget(self.screen_cap, 0, 2, 8, 2)

        self.main_layout.setColumnStretch(1, 1)
        # self.main_layout.setRowStretch(1, 1)
        self.main_layout.setColumnMinimumWidth(0, 100)
        self.main_layout.setColumnMinimumWidth(1, 100)
        self.main_layout.setColumnMinimumWidth(2, 200)
        self.main_layout.setColumnMinimumWidth(3, 500)

        self.current_frame = None

    @Slot(np.ndarray)
    def get_new_frame(self, frame):
        print("SNAPSHOT!")
        cv.imshow("Frame testing", frame)


def stop_trace():
    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()
    top_stats = snapshot.statistics("lineno")
    with open("memory_usage.txt", "w") as f:
        f.write("[ Top 10 memory consumers ]\n")
        for stat in top_stats[:10]:
            f.write(f"{stat}\n")
        # Detailed traceback for the top memory consumer
        f.write("\n[ Detailed traceback for the top memory consumer ]\n")
        for stat in top_stats[:1]:
            f.write("\n".join(stat.traceback.format()) + "\n")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QCoreApplication.setApplicationName("Testin")
    test = MainWindow()
    test.show()
    cap = ScreenCapturePreview()
    # cap.show()
    input("waiting...")
    sys.exit(app.exec())
