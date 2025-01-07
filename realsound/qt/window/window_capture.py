# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

from enum import Enum, auto

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
)
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtCore import QItemSelection, Qt, Slot, Signal
import numpy as np

from .screenlistmodel import ScreenListModel
from .windowlistmodel import WindowListModel


import time
import cv2 as cv


class ScreenCapturePreview(QWidget):

    frame_updated = Signal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lasttime = time.time()

        self._media_capture_session = QMediaCaptureSession(self)
        self._video_widget = QVideoWidget(self)
        self._video_widget_label = QLabel("Capture output:", self)
        self._start_stop_button = QPushButton(self)
        self._status_label = QLabel(self)

        # Setup QScreenCapture with initial source:
        self.setScreen(QGuiApplication.primaryScreen())
        self._media_capture_session.setVideoOutput(self._video_widget)

        self._window_list_view = QListView(self)
        self._window_capture = QWindowCapture(self)
        self.select_first_window()
        self._window_capture.start()
        self._media_capture_session.setWindowCapture(self._window_capture)
        self.update_active(True)
        self._window_label = QLabel("Select window to capture:", self)

        self._window_list_model = WindowListModel(self)
        self._window_list_view.setModel(self._window_list_model)
        update_action = QAction("Update windows List", self)
        update_action.triggered.connect(self._window_list_model.populate)
        self._window_list_view.addAction(update_action)
        self._window_list_view.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.select_first_window()

        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self._start_stop_button, 4, 0)
        grid_layout.addWidget(self._video_widget_label, 0, 1)
        grid_layout.addWidget(self._video_widget, 1, 1, 4, 1)
        grid_layout.addWidget(self._window_label, 2, 0)
        grid_layout.addWidget(self._window_list_view, 3, 0)
        grid_layout.addWidget(self._status_label, 5, 0, 1, 2)

        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(1, 1)
        grid_layout.setColumnMinimumWidth(0, 400)
        grid_layout.setColumnMinimumWidth(1, 400)
        grid_layout.setRowMinimumHeight(3, 1)

        selection_model = self._window_list_view.selectionModel()
        selection_model.selectionChanged.connect(
            self.on_current_window_selection_changed
        )

        self._window_capture.errorOccurred.connect(
            self.on_window_capture_error_occured, Qt.QueuedConnection
        )

        self._window_capture.captureSession().videoOutput().videoSink().videoFrameChanged.connect(
            self.on_frame_update
        )

    @Slot(QItemSelection)
    def on_current_window_selection_changed(self, selection):
        self.clear_error_string()
        indexes = selection.indexes()
        if indexes:
            window = self._window_list_model.window(indexes[0])
            if not window.isValid():
                m = "The window is no longer valid. Update the list of windows?"
                answer = QMessageBox.question(self, "Invalid window", m)
                if answer == QMessageBox.Yes:
                    self._window_list_view.clearSelection()
                    self._window_list_model.populate()
                    return
            self._window_capture.setWindow(window)
        else:
            self._window_capture.setWindow(QCapturableWindow())

    def select_first_window(self):
        window_list = QWindowCapture.capturableWindows()
        pong_window = [
            window
            for window in window_list
            if "Pong480" in window.description()  # Remove blank handles
        ]
        if pong_window:
            self._window_capture.setWindow(pong_window[0])
        else:
            self._window_capture.setWindow(window_list[0])

    @Slot(QWindowCapture.Error, str)
    def on_window_capture_error_occured(self, error, error_string):
        self.set_error_string("QWindowCapture: Error occurred " + error_string)

    def set_error_string(self, t):
        self._status_label.setStyleSheet("background-color: rgb(255, 0, 0);")
        self._status_label.setText(t)

    def clear_error_string(self):
        self._status_label.clear()
        self._status_label.setStyleSheet("")

    @Slot()
    def on_start_stop_button_clicked(self):
        self.get_frame_info()
        self.clear_error_string()
        self.update_active(not self.is_active())

    def update_start_stop_button_text(self):
        active = self.is_active()
        m = "Stop window capture" if active else "Start window capture"
        self._start_stop_button.setText(m)

    def update_active(self, active):
        self._window_capture.setActive(active)
        self.update_start_stop_button_text()

    def is_active(self):
        return self._window_capture.isActive()

    def get_frame_info(self):
        video_frame = (
            self._window_capture.captureSession().videoOutput().videoSink().videoFrame()
        )

        video_frame.map(QVideoFrame.MapMode.ReadOnly)
        bits = video_frame.bits(0)
        print(len(bits) / 8)
        print(
            f"{video_frame.width()}x{video_frame.height()}  \n total bytes: {len(bits) / 8} \nbytes per line: {video_frame.bytesPerLine(0)} \nbytes per pixel: {video_frame.bytesPerLine(0) / video_frame.width()}"
        )
        video_frame.unmap()
        print(video_frame.pixelFormat())

        # return dir(video_frame)

    def on_frame_update(self):
        if time.time() - self.lasttime > 0.016:
            video_frame = (
                self._window_capture.captureSession()
                .videoOutput()
                .videoSink()
                .videoFrame()
            )

            # map video frame from memory buffer
            #### DANGER ZONE
            video_frame.map(QVideoFrame.MapMode.ReadOnly)

            frame_small = cv.resize(
                np.reshape(
                    np.frombuffer(video_frame.bits(0), dtype=np.ubyte),
                    (video_frame.height(), video_frame.bytesPerLine(0) // 4, 4),
                ),
                (0, 0),
                fx=0.5,
                fy=0.5,
            )

            self.frame_updated.emit(frame_small)
            video_frame.unmap()
            #### DANGER ZONE
            self.lasttime = time.time()
