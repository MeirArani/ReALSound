from math import sqrt
from realsound.cv import harris
import enum
import cv2
import numpy as np
from importlib import resources
from realsound import config
from itertools import takewhile
from realsound.core import DecisionLayer


class VisionLayer:
    def __init__(self):
        pass

    def see(self, frame, settings):
        # Get object corners using harris algorithm
        corners = harris.get_corners(frame, settings)

        # Identify object shapes using corners
        shapes = harris.detect(np.reshape(corners, (-1, 2)), frame.shape)

        # Classify Entities (i.e. ball & paddles) from shapes
        return harris.classify(shapes)


class AudificationLayer:
    def __init__(self):
        pass

    def play(self, audio_objects):
        pass


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
    print("hi!")
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
        cv2.waitKey(1000 // frame_rate)
