import cv2
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QVideoFrame
import time

from numpy import ndarray

# TODO: Make this a QObject that can hook up to slots and send signals


class VideoSource(QObject):

    send_new_frame = Signal(ndarray)

    def __init__(self, filename, start_pos=0, frame_rate=60, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.start_pos = start_pos
        self.frame_rate = frame_rate
        self.cap = cv2.VideoCapture(filename)

    def start(self):
        print("Thread started!")
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_pos)
        if not self.cap.isOpened():
            print("File Error")
            return

        while True:
            time.sleep(1 / self.frame_rate)

            ret, frame = self.cap.read()

            if not ret:
                self.cap.release()
                print("Out of frames!")
                break

            self.send_new_frame.emit(frame)

    def send_first_frame(self):
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
