from enum import IntEnum
import time
import numpy as np
import cv2

from PySide6.QtCore import Slot, Signal, QObject
from realsound.core import Paddle, Ball


MOE = 2
PADDLE_X_MOE = 18
PADDLE_Y_MOE = 15
GOAL_PIXEL_THRESH = 60
PADDLE_MAX_HEIGHT = 40
START_FRAME = 70
PADDLE_MAX_WIDTH = 15
OUT_OF_GAME_MIN_FRAMES = 2
FRAME_RATE = 24
MAX_DELTA = 300

# EVENTS
# CV EVENTS
cv_event_frame_updated = Signal(np.ndarray, int)

# SOUND EVENTS

# BALL MOVEMENT/HIT
sound_event_ball_moved = Signal(float, float)
sound_event_ball_toggle = Signal(bool)
sound_event_ball_hit = Signal(bool)


def process(self, frame, settings):

    # Get Entity corners
    # Uses Harris Corner Detection
    corners = self.get_corners(frame, settings)

    # Detect object shapes
    # Need to re-shape array to make function happy
    shapes = self.detect(np.reshape(corners, (-1, 2)), frame.shape)

    # Classify Entities (i.e. ball & paddles)
    return self.classify(shapes)


def get_corners(self, frame, settings):
    self.threshold = settings["thresh"] / 100

    # Get a grayscale copy
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Find corners using harris corner detector
    corners = cv2.goodFeaturesToTrack(
        gray, settings["points"], settings["thresh"] / 1000, settings["distance"]
    )

    return corners


def detect(self, points, frame_shape):
    candidates = points  # Grab a copy
    # Where we store our final results
    results = np.zeros((3, 4, 2), dtype=np.int64)
    for index, i in enumerate(points):  # For each point in our original array

        # If we've already found this point, move on
        if np.argwhere(np.any(results == i, axis=2)).size > 0:
            continue

        # Initialize our result array
        result = np.zeros((4, 2), dtype=np.int64)
        result[0] = i  # Set first point
        # Compares X Y values
        # finds point that only shares ONE X or ONE Y--since its a rectangle
        test_points = candidates[
            np.argwhere(
                np.logical_xor(
                    self.is_close(candidates, i)[:, 0],
                    self.is_close(candidates, i)[:, 1],
                )
            ).flatten()
        ]

        # we got back two actual points,
        # they also don't share X/Y values
        # (Since they're opposite corners of the rect)
        if test_points.shape[0] > 1 and not np.any(
            self.is_close(test_points[:, 0], test_points[:, 1])
        ):
            if test_points.shape[0] > 2:
                # test_points[np.argsort(
                # np.sum(abs(test_points - i), axis=1))][:2]
                test_points = test_points[np.argmin(abs(test_points - i), axis=0)]

            # append our new points to the resulting object
            result[1:3] = test_points

            # Get the two X/Y values from our two connected points
            # They *aren't* close to our first point,
            # which would be the opposite corner of the rectangle
            # Aka our forth point that closes the rect
            p4 = test_points[np.where(self.is_close(test_points, i) != True)]

            # Make sure the X / Y in p4 are in the right order
            if not np.any(p4[0] == test_points[:, 0]):
                p4 = np.flip(p4)  # if not, swap X/Y values
            result[3] = p4  # save to results

            maxes = np.max(result, axis=0)  # Find maxes
            mins = np.min(result, axis=0)  # find mins

            # Subtract mins from maxes
            # figures out length and width of box.
            # Then, Divide by dimensions of screen
            horz_rt = (maxes[0] - mins[0]) / frame_shape[1]
            vert_rt = (maxes[1] - mins[1]) / frame_shape[0]

            # If the box isn't illogically large.
            # If it is, we had a rare misfire of alignments
            # Build final result in correct order, based on maxes
            if (
                horz_rt < self.PADDLE_MAX_WIDTH / frame_shape[1]
                and vert_rt < self.PADDLE_MAX_HEIGHT / frame_shape[0]
            ):
                result = np.array(
                    [
                        [mins[0], mins[1]],
                        [mins[0], maxes[1]],
                        [maxes[0], mins[1]],
                        [maxes[0], maxes[1]],
                    ],
                    dtype=np.int64,
                )
                # Add to the list of results at the closest empty slot
                results[
                    np.argwhere(np.all(np.all(results == 0, axis=1), axis=1))[0]
                ] = result
                candidates = candidates[
                    np.argwhere(
                        np.all(
                            np.any(
                                np.logical_not(
                                    self.is_close(result[:, None], candidates)
                                ),
                                axis=2,
                            ),
                            axis=0,
                        )
                    )
                ][
                    :, 0, :
                ]  # Remove resultant points from candidate list
    return results[np.argwhere(np.all(np.any(results != 0, axis=2), axis=1))][:, 0, :]


def classify(self, groups):
    # Returns a list of three objects: Paddle1 (left), Paddle2 (right), & ball
    # Objects are np arrays with their 4 corners.
    # Starts top left, winds CCW.
    results = [None, None, None]
    if len(groups) == 0:
        return results

    # Get widths/heights of each object
    # To Distinguish paddles from balls
    w = groups[:, 2, 0] - groups[:, 0, 0]
    h = groups[:, 1, 1] - groups[:, 0, 1]

    # Check for ball
    ball = groups[np.argwhere(h / w < 2)].squeeze()
    if len(ball) == 4:
        results[2] = Ball(ball)

    # Check for paddles
    paddles = groups[np.argwhere(h / w > 2)].squeeze()
    if len(paddles) == 2:
        # Order paddles by direction (left first)
        if paddles[0][0][0] < self.cap_w / 2:
            results[0] = Paddle(paddles[0])
            results[1] = Paddle(paddles[1])
        else:
            results[0] = Paddle(paddles[1])
            results[1] = Paddle(paddles[0])
    return results


def add_text(self, frame, text, pos, scale=1):
    # Mark text
    cv2.putText(
        frame,
        text,
        pos,
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2,
    )


def display_frame_count(self, frame, count):
    self.add_text(frame, "%r" % (count), (450, 80))


def display_state(self, frame, state):
    self.add_text(frame, "%r" % (state), (250, 80), 0.8)


def show_circles(self, frame, corners):
    for i in corners:
        x, y = i.ravel()
        cv2.circle(frame, (x, y), 3, 255, -1)


def is_close(self, p1, p2):
    return abs(p1 - p2) <= self.MOE
