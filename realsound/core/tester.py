import sys
from realsound.cv import harris, VideoReader, VideoWidget
import cv2
import numpy as np
from importlib import resources
from realsound import config
from itertools import takewhile
from realsound.core import DecisionLayer

from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import (
    QCapturableWindow,
    QMediaCaptureSession,
    QScreenCapture,
    QVideoFrame,
    QWindowCapture,
    QMediaRecorder,
    QVideoFrameInput,
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


def read_from_video(filename, start_frame=0):
    cap = cv2.VideoCapture(filename)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    if not cap.isOpened():
        print("File Error")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.release()
            print("Out of frames!")
            yield None
        yield frame, cap.get(cv2.CAP_PROP_POS_FRAMES)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = VideoWidget()
    widget.start()
    widget.show()
    app.exec()

    """print("hi!")
    frame_rate = 60
    gsm = DecisionLayer()
    cap = read_from_video(resources.files(config).joinpath("Pong480.mp4"), 1400)
    for frame, frame_number in takewhile(
        lambda next_frame: next_frame is not None, cap
    ):

        harris.add_text(frame, f"{frame_number}", (50, 50))

        objects = harris.detect(frame)

        new_corners = harris.classify(objects)
        gsm.decide(new_corners, frame)

        cv2.imshow("Testing", frame)
        cv2.waitKey(1000 // frame_rate)"""
