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

from realsound.cv import NewPong, PongVideoTest
from realsound.cv.PongVideo import GameState
from realsound.qt.cv import CVSettingsListWidget

from realsound.qt.capture import WindowCaptureWidget

import numpy as np

import cv2 as cv

from realsound.qt.cv import CVStatsWidget


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame_counter = 0
        self.settings_label = QLabel("CV Settings", self)
        self.stats_label = QLabel("Stats", self)
        self.settings = CVSettingsListWidget(default_config="cv_settings.json")
        self.screen_cap = WindowCaptureWidget()
        # self.screen_cap.frame_updated.connect(self.get_new_frame)

        self.stats = CVStatsWidget()

        self.main_layout = QGridLayout(self)
        self.main_layout.addWidget(self.settings_label, 0, 0)
        self.main_layout.addWidget(self.settings, 1, 0, 2, 1)
        self.main_layout.addWidget(self.stats_label, 3, 0)
        self.main_layout.addWidget(self.stats, 4, 0)
        self.main_layout.addWidget(self.screen_cap, 0, 2, 8, 2)

        self.main_layout.setColumnStretch(1, 1)
        # self.main_layout.setRowStretch(1, 1)
        self.main_layout.setColumnMinimumWidth(0, 100)
        self.main_layout.setColumnMinimumWidth(1, 100)
        self.main_layout.setColumnMinimumWidth(2, 200)
        self.main_layout.setColumnMinimumWidth(3, 500)

        # self.cv_client = NewPong(self.settings)

        # self.screen_cap.frame_updated.connect(self.cv_client.on_new_frame)

        # self.current_frame = None

        self.pong_video = PongVideoTest(
            r"C:\Users\cloud\source\repos\CVPongDemo\PongDemoPy\Pong480.mp4",
            self.settings,
        )

        self.pong_video.frame_updated.connect(self.stats.update_stats)

    @Slot(np.ndarray)
    def get_new_frame(self, frame):
        pass
        # cv.imshow("CV Output", frame)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QCoreApplication.setApplicationName("ReAL Sound")
    main_window = MainWindow()

    main_window.show()

    main_window.pong_video.start()

    if app.exec() == 0:

        main_window.pong_video.stop()
        main_window.screen_cap.stop()
        sys.exit(0)
