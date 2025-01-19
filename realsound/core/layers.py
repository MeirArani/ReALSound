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
        self.current_state = self.attract

    def decide(self, entities):
        self.current_state = self.current_state(entities)

    # State logic
    def attract(self, data):
        print("ATTRACT!")
        return self.intermission if has_paddles(data) else self.attract

    def intermission(self, data):  # Curse you break statement
        print("INTERMISSION!")
        return self.match if has_ball(data) else self.intermission

    def match(self, data):
        return self.goal if scored_goal(data) else self.match

    def goal(self, data):
        print("GOAL!")
        return self.intermission

    def win(self, data):
        print("WIN!")
        return self.attract


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


def has_paddles(entities):
    return entities[0] is not None and entities[1] is not None


def has_ball(entities):
    return entities[2] is not None


def scored_goal(entities):
    if has_paddles(entities) and has_ball(entities):
        if entities[2].position[0] > entities[1].corners:
            print("P2 GOAL!")
            return True
        elif entities[2].position[0] < entities[0].corners:
            return True
    return False


if __name__ == "__main__":
    print("hi!")
    gsm = DecisionLayer()
    cap = read_from_video(resources.files(config).joinpath("Pong480.mp4"))
    for frame in takewhile(lambda next_frame: next_frame is not None, cap):
        objects = harris.detect(frame)

        entities = harris.classify(objects)

        gsm.decide(entities)

        cv2.imshow("Testin", frame)
        cv2.waitKey(60)
