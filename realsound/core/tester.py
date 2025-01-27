from numbers import Real
import sys
from realsound.cv import VideoWidget
import cv2
import numpy as np
from importlib import resources
from realsound import config
from itertools import takewhile
from realsound.core import DecisionLayer
from PySide6.QtWidgets import QApplication

from realsound.core.client import RealSound
from realsound.core.dummy import VideoSource

import threading


def new_test():

    START_FRAME = 1398
    FRAME_RATE = 20

    app = QApplication(sys.argv)
    client = RealSound(START_FRAME)

    # Video Dummy
    file = resources.files(config).joinpath("Pong480.mp4")
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
    new_test()
