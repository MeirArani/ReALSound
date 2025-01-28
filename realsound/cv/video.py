import cv2
from PySide6.QtCore import Slot, Signal, QObject
from PySide6.QtMultimedia import QVideoFrame
from PySide6.QtGui import QImage
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import (
    QCapturableWindow,
    QMediaCaptureSession,
    QScreenCapture,
    QVideoFrame,
    QWindowCapture,
    QMediaRecorder,
    QVideoFrameInput,
    QVideoFrameFormat,
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
from PySide6.QtCore import QCoreApplication, Slot, QSize
from importlib import resources
from realsound import resources
from itertools import takewhile
import time
from numpy import ndarray


class VideoWidget(QWidget):

    frame_ready = Signal(QVideoFrame)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up GUI Widgets
        self.capture = QMediaCaptureSession()
        self.recorder = QMediaRecorder()
        self.video_input = QVideoFrameInput(
            QVideoFrameFormat(
                QSize(720, 480), QVideoFrameFormat.PixelFormat.Format_BGRX8888
            )
        )
        self.video_output = QVideoWidget()

        # self.generator = VideoReader(filename, start_frame)

        self.capture.setRecorder(self.recorder)
        self.capture.setVideoFrameInput(self.video_input)
        self.capture.setVideoOutput(self.video_output)

        # self.video_input.readyToSendVideoFrame.connect(self.generator.send)
        # self.generator.frame_ready.connect(self.video_input.sendVideoFrame)

        grid_layout = QGridLayout(self)

        grid_layout.addWidget(self.video_output, 0, 0)
        grid_layout.setRowMinimumHeight(0, 300)
        grid_layout.setColumnMinimumWidth(0, 300)
        self.frame_ready.connect(self.video_input.sendVideoFrame)

        self.recorder.record()

    def send(self):
        pass

    def read(self, frame, frame_pos=0):
        pass

    @Slot(ndarray)
    def display(self, frame):
        height, width, _ = frame.shape
        bytes_per_line = frame.strides[0]
        q_img = QImage(
            frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888
        )
        self.frame_ready.emit(QVideoFrame(q_img))
