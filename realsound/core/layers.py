from realsound.cv import harris
import enum
import cv2
import numpy as np
from importlib import resources
from realsound import config
from itertools import takewhile


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


class DecisionLayer:
    def __init__(self):
        pass

    def decide(self, entities):
        pass


class AudificationLayer:
    def __init__(self):
        pass

    def play(self, audio_objects):
        pass


def process_frame(self, frame):

    key = 0xFF & cv2.waitKey(1)
    if key == ord("q"):
        self.running = False
    elif key == ord("p"):
        self.paused = not self.paused
    elif key == ord("c"):
        show_circles = not show_circles
    while self.paused:
        key = 0xFF & cv2.waitKey(1)
        if key == ord("s"):
            break
        elif key == ord("p"):
            self.paused = not self.paused
        elif key == ord("c"):
            show_circles = not show_circles


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
        yield frame

    # State logic
    def attract(data):
        yield data

    def intermission(data):  # Curse you break statement
        yield data

    def match(data):
        yield data

    def goal(data):
        yield data

    def win(data):
        yield data


if __name__ == "__main__":
    print("hi!")
    cap = read_from_video(resources.files(config).joinpath("Pong480.mp4"))
    for frame in takewhile(lambda next_frame: next_frame is not None, cap):
        ents = harris.detect(frame)
        # cv2.imshow("Testin", frame)
        # cv2.waitKey(30)
