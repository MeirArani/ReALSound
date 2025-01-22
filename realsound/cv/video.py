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
from realsound import config
from itertools import takewhile
import time


class VideoWidget(QWidget):
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

        self.generator = VideoReader(resources.files(config).joinpath("Pong480.mp4"), 0)

        self.capture.setRecorder(self.recorder)
        self.capture.setVideoFrameInput(self.video_input)
        self.capture.setVideoOutput(self.video_output)

        self.video_input.readyToSendVideoFrame.connect(self.generator.send)
        self.generator.frame_ready.connect(self.video_input.sendVideoFrame)

        grid_layout = QGridLayout(self)

        grid_layout.addWidget(self.video_output, 0, 0)
        grid_layout.setRowMinimumHeight(0, 300)
        grid_layout.setColumnMinimumWidth(0, 300)
        self.video_input.sendVideoFrame(self.generator.read())

    def start(self):
        self.recorder.record()


class VideoReader(QObject):

    frame_ready = Signal(QVideoFrame)

    def __init__(self, filename, start_frame=0, parent=None):
        # Set up Video capture
        super().__init__(parent)
        self.cap = cv2.VideoCapture(filename)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        if not self.cap.isOpened():
            print("File error!")

    @Slot()
    def send(self):
        self.frame_ready.emit(self.read())

    @Slot()
    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            print("Out of frames!")
            return None
        height, width, _ = frame.shape
        bytes_per_line = frame.strides[0]
        q_img = QImage(
            frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888
        )
        return QVideoFrame(q_img)
