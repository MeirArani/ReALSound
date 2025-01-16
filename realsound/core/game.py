from realsound.core import FSM, State
import enum
import cv2


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


def read_from_video(self, filename, start_frame=0):
    cap = cv2.VideoCapture(self.video)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    if not cap.isOpened():
        print("File Error")
        return

    while True:
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            print("Frame error!")
            break
        process_frame(frame)


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
