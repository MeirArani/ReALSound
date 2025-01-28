import numpy as np
from PySide6.QtCore import QObject
import cv2
import json
from importlib import resources
from PySide6.QtCore import Slot, Signal, QObject
from realsound import config

# CV Functions

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


default_settings = {
    name: settings["value"]
    for name, settings in json.loads(
        resources.read_text(config, "cv_settings.json")
    ).items()
}


# Basic wrapper object for vision functions
class VisionLayer(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.client = parent

    def see(self, frame):
        # Identify object shapes using corners
        shapes = detect(frame)

        # Classify Entities (i.e. ball & paddles) from shapes
        return classify(shapes)


def detect(frame, settings=default_settings):
    # Get a grayscale copy
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Find corners using harris corner detector
    corners = cv2.goodFeaturesToTrack(
        gray, settings["points"], settings["thresh"] / 100, settings["distance"]
    ).squeeze()

    candidates = corners  # Our candidates are *all* corners at first
    # Where we store our final results
    results = np.zeros((3, 4, 2), dtype=np.int64)
    for index, i in enumerate(corners):  # For each point in our original array

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
                    is_close(candidates, i)[:, 0],
                    is_close(candidates, i)[:, 1],
                )
            )
        ].squeeze()

        # we got back two actual points,
        # they also don't share X/Y values
        # (Since they're opposite corners of the rect)
        if (
            test_points.shape[0] > 1
            and len(test_points.shape) > 1
            and not np.any(is_close(test_points[:, 0], test_points[:, 1]))
        ):
            if test_points.shape[0] > 2:
                # test_points[np.argsort(
                # np.sum(abs(test_points - i), axis=1))][:2]
                # Find the points closest to i
                test_points = test_points[np.argmin(abs(test_points - i), axis=0)]

            # append our new points to the resulting object
            result[1:3] = test_points

            # Get the two X/Y values from our two connected points
            # They *aren't* close to our first point,
            # which would be the opposite corner of the rectangle
            # Aka our forth point that closes the rect
            p4 = test_points[np.where(is_close(test_points, i) != True)]

            # Make sure the X / Y in p4 are in the right order
            if not np.any(p4[0] == test_points[:, 0]):
                p4 = np.flip(p4)  # if not, swap X/Y values
            result[3] = p4  # save to results

            maxes = np.max(result, axis=0)  # Find maxes
            mins = np.min(result, axis=0)  # find mins

            # Subtract mins from maxes
            # figures out length and width of box.
            # Then, Divide by dimensions of screen
            horz_rt = (maxes[0] - mins[0]) / frame.shape[1]
            vert_rt = (maxes[1] - mins[1]) / frame.shape[0]

            # If the box isn't illogically large.
            # If it is, we had a rare misfire of alignments
            # Build final result in correct order, based on maxes
            if (
                horz_rt < PADDLE_MAX_WIDTH / frame.shape[1]
                and vert_rt < PADDLE_MAX_HEIGHT / frame.shape[0]
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
                # Remove found points from candidate list
                candidates = candidates[
                    np.invert(
                        is_close(result[:, None], candidates).all(axis=2).any(axis=0)
                    )
                ]
    return results[np.argwhere(np.all(np.any(results != 0, axis=2), axis=1))][:, 0, :]


def classify(groups):
    # Returns a list of three objects: Paddle1 (left), Paddle2 (right), & ball
    # Objects are np arrays with their 4 corners.
    # Starts top left, winds CCW.
    results = {"p1": None, "p2": None, "ball": None}
    if len(groups) == 0:
        return results

    # Get widths/heights of each object
    # To Distinguish paddles from balls
    w = groups[:, 2, 0] - groups[:, 0, 0]
    h = groups[:, 1, 1] - groups[:, 0, 1]

    # Check for ball
    ball = groups[np.argwhere(h / w < 2)].squeeze()
    if len(ball) == 4:
        results["ball"] = ball

    # Check for paddles
    paddles = groups[np.argwhere(h / w > 2)].squeeze()
    if len(paddles) == 2:
        # Order paddles by direction (left first)
        if paddles[0][0][0] < paddles[1][0][0]:
            results["p1"] = paddles[0]
            results["p2"] = paddles[1]
        else:
            results["p1"] = paddles[1]
            results["p2"] = paddles[0]
    return results


def is_close(p1, p2):
    return abs(p1 - p2) <= MOE
