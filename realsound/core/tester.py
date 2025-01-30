from numbers import Real
import sys
from realsound.cv import VideoWidget
import cv2
import numpy as np
from importlib import resources
from realsound.resources import video
from itertools import takewhile
from realsound.core import DecisionLayer
from PySide6.QtWidgets import QApplication, QWidget

from realsound.core.client import RealSound
from realsound.core.dummy import VideoSource

import threading

from realsound.qt.audio import AudioWidget


class PitchTest(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._audio = AudioWidget()


def spawn_pitch():

    app = QApplication(sys.argv)
    widget = AudioWidget()
    widget.show()
    sys.exit(app.exec())


def new_test():

    START_FRAME = 900
    FRAME_RATE = 25

    app = QApplication(sys.argv)
    client = RealSound(START_FRAME)

    # Video Dummy
    file = resources.files(video).joinpath("Pong480.mp4")
    input = VideoSource(file, START_FRAME, FRAME_RATE)

    # Hook video dummy output to client
    input.send_new_frame.connect(client.on_new_frame)

    # Spawn a new thread to read the video frames
    frame_generator = threading.Thread(target=input.start)

    # Hack-y code needed to make video playback happy
    # Sends initial frame to kickstart event loop
    client.video_out.video_input.sendVideoFrame(input.send_first_frame())

    frame_generator.start()

    client.show()
    app.exec()


if __name__ == "__main__":
    # spawn_pitch()
    new_test()
