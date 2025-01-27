import sys
from importlib import resources
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

import main
from realsound import config
from realsound.cv import NewPong, VisionLayer
from realsound.qt.cv import CVSettingsListWidget

from realsound.qt.capture import WindowCaptureWidget, WindowCaptureListWidget

import numpy as np

import cv2 as cv2

from realsound.qt.cv import CVStatsWidget

from realsound.qt.audio import AudioWidget


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame_counter = 0

        self.settings = CVSettingsListWidget(default_config="cv_settings.json")

        self.stats = CVStatsWidget()

        self.audio_settings = AudioWidget()

        self.screen_cap = WindowCaptureWidget()

        self.screen_list = WindowCaptureListWidget()

        self.screen_list.update_window.connect(
            self.screen_cap.on_current_window_selection_changed
        )
        self.screen_list.update_active_status.connect(
            self.screen_cap.on_active_state_changed
        )

        self.screen_cap._window_capture.errorOccurred.connect(
            self.screen_list.on_window_capture_error_occured
        )

        self.screen_cap._window_capture.errorOccurred.connect(self.screen_cap.reboot)

        self.screen_cap._window_capture.setActive(True)

        # self.screen_cap.frame_updated.connect(self.get_new_frame)

        self.main_layout = QGridLayout(self)

        # Col 1: CV Settings/WindowList
        self.main_layout.addWidget(self.settings, 0, 0)

        self.main_layout.addWidget(self.screen_list, 1, 0)

        # Col 2: Window preview + Stats

        self.main_layout.addWidget(self.screen_cap, 0, 1)

        self.main_layout.addWidget(self.stats, 1, 1)

        # Col 3: Audio Settings

        self.main_layout.addWidget(self.audio_settings, 0, 2)

        self.main_layout.setRowStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setColumnMinimumWidth(0, 300)

        # self.cv_client = NewPong(self.settings)

        # self.screen_cap.frame_updated.connect(self.cv_client.on_new_frame)

        # self.current_frame = None

        self.video_file = resources.files(config).joinpath("Pong480.mp4")
        self.vision = VisionLayer(
            self.settings,
        )

        self.vision.cv_event_frame_updated.connect(self.stats.update_stats)

        self.vision.sound_event_ball_moved.connect(
            self.audio_settings.update_ball_sound_position
        )
        self.vision.sound_event_goal_scored.connect(self.audio_settings.play_goal)

        self.vision.sound_event_ball_hit.connect(self.audio_settings.play_hit)

        self.vision.sound_event_ball_toggle.connect(
            self.audio_settings.toggle_ball_sound
        )

        self.cap = None

    @Slot(np.ndarray)
    def get_new_frame(self, frame):
        pass
        # cv.imshow("CV Output", frame)

    def simulate_stream(self):
        pass

    def get_vision_settings(self):
        return {key: value.slider.value for key, value in self.settings.settings}

    def scratch(self):
        # frame = Got a frame
        # entities = vision.see(frame, settings)
        # audio_objects = decision.decide(entities)
        # audification.play(audio_objects)
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)

    QCoreApplication.setApplicationName("ReAL Sound")
    main_window = MainWindow()

    main_window.show()

    main_window.cap = cv2.VideoCapture(main_window.video_file)
    main_window.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    main_window.vision.start()

    if app.exec() == 0:

        main_window.vision.stop()
        main_window.screen_cap.stop()
        sys.exit(app.exec())
