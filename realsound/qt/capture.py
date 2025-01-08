# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations
from operator import is_


from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import (
    QCapturableWindow,
    QMediaCaptureSession,
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
from PySide6.QtCore import QItemSelection, Qt, Slot, Signal, QAbstractListModel

import numpy as np


import time
import cv2 as cv


class WindowCaptureWidget(QWidget):

    frame_updated = Signal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lasttime = time.time()

        self._media_capture_session = QMediaCaptureSession(self)
        self._video_widget = QVideoWidget(self)
        self._video_widget_label = QLabel("Capture output:", self)

        # Setup QScreenCapture with initial source:
        self.setScreen(QGuiApplication.primaryScreen())
        self._media_capture_session.setVideoOutput(self._video_widget)

        self._window_capture = QWindowCapture(self)
        self.select_first_window()
        self._window_capture.start()
        self._media_capture_session.setWindowCapture(self._window_capture)

        self.select_first_window()

        grid_layout = QGridLayout(self)

        grid_layout.addWidget(self._video_widget_label, 0, 0)
        grid_layout.addWidget(self._video_widget, 1, 0, 3, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setRowStretch(1, 1)
        grid_layout.setColumnMinimumWidth(0, 400)
        grid_layout.setRowMinimumHeight(1, 200)

        self._window_capture.captureSession().videoOutput().videoSink().videoFrameChanged.connect(
            self.on_frame_update
        )

    @Slot(QCapturableWindow)
    def on_current_window_selection_changed(self, window):
        self.clear_error_string()
        self._window_capture.setWindow(window)

    @Slot(bool)
    def on_active_state_changed(self, is_active):
        self._window_capture.setActive(is_active)

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

    def stop(self):
        self._window_capture.stop()


class WindowCaptureListWidget(QWidget):

    update_window = Signal(QCapturableWindow)
    update_active_status = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._list_label = QLabel("Select window to capture:", self)
        self._start_stop_button = QPushButton(self)
        self._status_label = QLabel(self)

        self._window_list_view = QListView(self)

        self.is_stream_active = True
        self.update_active(self.is_stream_active)

        self._window_list_model = WindowListModel(self)
        self._window_list_view.setModel(self._window_list_model)
        update_action = QAction("Update windows List", self)
        update_action.triggered.connect(self._window_list_model.populate)
        self._window_list_view.addAction(update_action)
        self._window_list_view.setContextMenuPolicy(Qt.ActionsContextMenu)

        grid_layout = QGridLayout(self)

        grid_layout.addWidget(self._list_label, 0, 0)
        grid_layout.addWidget(self._window_list_view, 1, 0)
        grid_layout.addWidget(self._start_stop_button, 2, 0)
        grid_layout.addWidget(self._status_label, 3, 0, 1, 2)

        selection_model = self._window_list_view.selectionModel()
        selection_model.selectionChanged.connect(
            self.on_current_window_selection_changed
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
            self.update_window.emit(window)
        else:
            self.update_window.emit(QCapturableWindow())

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
        self.clear_error_string()
        self.update_active(not self.is_stream_active)

    def update_start_stop_button_text(self):
        active = self.is_stream_active
        m = "Stop window capture" if active else "Start window capture"
        self._start_stop_button.setText(m)

    def update_active(self, active):
        self.is_stream_active = active
        self.update_active_status.emit(active)
        self.update_start_stop_button_text()


class WindowListModel(QAbstractListModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._window_list = QWindowCapture.capturableWindows()
        self._window_list = [
            window
            for window in self._window_list
            if "Window 0x" not in window.description()  # Remove blank handles
        ]

    def rowCount(self, QModelIndex):
        return len(self._window_list)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            window = self._window_list[index.row()]
            return window.description()
        return None

    def window(self, index):
        return self._window_list[index.row()]

    @Slot()
    def populate(self):
        self.beginResetModel()
        self._window_list = QWindowCapture.capturableWindows()
        self.endResetModel()
