import numpy as np
from numpy import ndarray
import cv2
from PySide6.QtCore import Slot

from enum import IntEnum


class NewPong:
    MOE = 2
    PADDLE_X_MOE = 18
    PADDLE_Y_MOE = 15
    GOAL_PIXEL_THRESH = 60
    PADDLE_MAX_HEIGHT = 40
    START_FRAME = 0
    PADDLE_MAX_WIDTH = 15
    OUT_OF_GAME_MIN_FRAMES = 2

    def __init__(self, settings, video=None):
        self.qt_settings = settings
        self.paused = False
        self.good_frame = False
        self.frame_state = GameState.NONE
        self.bad_frames = []
        self.out_of_game_frames = 0

        self.last_hit_check = 0
        self.in_hit_check = False
        self.is_left_hit = False
        self.hit_position = None
        self.hit_max_frames = 4
        self.goal_scored = False
        self.p1_score = 0
        self.p2_score = 0
        self.video = video
        self.last_good_objs = np.zeros((3, 4, 2), np.int64)
        self.show_circles = False
        self.corners = None

        self.frame_counter = 0
        self.paddle_img = cv2.imread(
            "C:\\Users\\cloud\\source\\repos\\ReALSound\\realsound\\config\\insta.jpg",
            cv2.IMREAD_COLOR,
        )
        self.ball_img = cv2.imread(
            "C:\\Users\\cloud\\source\\repos\\ReALSound\\realsound\\cv\\ball.png",
            cv2.IMREAD_COLOR,
        )

    def start(self, window_name="Pong Demo"):
        pass

    # capture, frame by frame (sick guitar riff)
    @Slot(ndarray)
    def on_new_frame(self, frame):

        # Mark text
        # self.add_text(frame, "%r" % (self.frame_counter), (450, 80))
        # print(self.paddle_img)

        result = cv2.matchTemplate(
            cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR),
            self.paddle_img,
            cv2.TM_CCOEFF_NORMED,
        )

        loc = np.where(result >= self.get_setting("thresh") / 100)

        x, w, h = self.paddle_img.shape[::-1]
        for pt in zip(*loc[::-1]):
            cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
        # Show image
        cv2.imshow("Frame testing", frame)

        self.frame_counter += 1

    # capture, frame by frame (sick guitar riff)
    @Slot(ndarray)
    def on_new_frameOLD(self, frame):
        # Get frame info
        self.frame_width = np.shape(frame)[1]
        self.frame_height = np.shape(frame)[0]
        self.VERT_MAX = self.PADDLE_MAX_HEIGHT / self.frame_height
        self.HORZ_MAX = self.PADDLE_MAX_WIDTH / self.frame_width

        # Mark text
        self.add_text(frame, "%r" % (self.frame_counter), (450, 80))

        # Reset state info
        self.good_frame = False
        self.threshold = self.get_setting("thresh") / 100

        # Get Gray Conversion
        self.treated_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Do Object Detection
        corners = cv2.goodFeaturesToTrack(
            self.treated_frame,
            self.get_setting("points"),
            self.get_setting("thresh") / 1000,
            self.get_setting("distance"),
        )
        # print(corners)
        groups = self.group_points(corners)
        # print(groups)

        objs = self.detect_objects(frame, groups)
        self.draw_circles(frame, corners, True)

        # Show image
        cv2.imshow("Frame testing", frame)

        self.frame_counter += 1

    def on_frame_update():
        pass

    def is_close(self, p1, p2):
        return abs(p1 - p2) <= self.MOE

    def group_points(self, points):
        shaped = np.reshape(points, (-1, 2))  # Clean points
        candidates = shaped  # Grab a copy
        # Where we store our final results
        results = np.zeros((3, 4, 2), dtype=np.int64)
        for index, i in enumerate(shaped):  # For each point in our original array

            # If we've already found this point, move on
            if np.argwhere(np.any(results == i, axis=2)).size > 0:
                continue

            # p2 = None  # Second point
            # p3 = None  # third point
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
                # min_max = np.array(
                #   [np.min(result, axis=0), np.max(result, axis=0)])
                maxes = np.max(result, axis=0)  # Find maxes
                mins = np.min(result, axis=0)  # find mins
                # Subtract mins from maxes
                # figures out length and width of box.
                # Then, Divide by dimmensions of screen
                horz_rt = (maxes[0] - mins[0]) / self.frame_width
                vert_rt = (maxes[1] - mins[1]) / self.frame_height  # Same for height
                # If the box isn't illogically large.
                # If it is, we had a rare misfire of alignments
                # Build final result in correct order, based on maxes
                if horz_rt < self.HORZ_MAX and vert_rt < self.VERT_MAX:
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
        return results[np.argwhere(np.all(np.any(results != 0, axis=2), axis=1))][
            :, 0, :
        ]

    def detect_objects(self, frame, groups):
        # Four data points: detected, Ball, Paddle1 (left), Paddle2 (right)
        # detected encodes if the next three objects were detected
        # in a single number ranging from 0-7
        # The number is a binary representation of the three objects:
        # All three yield 7 (111) while none yield 0 (000).
        # 6 = Ball + L paddle (110) 5 = Ball + R paddle (101),
        # 4 = Ball (100), 3 = Paddles (011), 2/1 = LP/RP (010/001)
        # The next indexes store the top left corner of the object
        # as well as its width and height
        self.frame_state = GameState.NONE
        results = np.zeros((3, 4, 2))
        if len(groups) == 0:
            return results
        w = groups[:, 2, 0] - groups[:, 0, 0]
        h = groups[:, 1, 1] - groups[:, 0, 1]
        paddles = groups[np.argwhere(h / w > 2)][:, 0, :]
        paddles = np.take_along_axis(paddles, np.argsort(paddles, axis=1), axis=1)
        ball = groups[np.argwhere(h / w < 2)][:, 0, :]
        if np.any(ball) and len(ball) == 1:
            cv2.rectangle(frame, ball[0][0], ball[0][3], (255, 0, 0), -1)
            self.frame_state += GameState.BALL
            results[2] = ball
        if np.any(paddles) and len(paddles) > 0:
            if len(paddles) == 2:
                cv2.rectangle(frame, paddles[0][0], paddles[0][3], (0, 255, 0), -1)
                cv2.rectangle(frame, paddles[1][0], paddles[1][3], (0, 255, 0), -1)
                self.frame_state += GameState.PADDLES
                if paddles[0][0][0] < self.frame_width / 2:
                    results[0] = paddles[0]
                    results[1] = paddles[1]
                else:
                    results[0] = paddles[1]
                    results[1] = paddles[0]
            elif len(paddles) == 1:
                pass
        # We have paddle movement or paddle and ball movement
        if self.frame_state in [GameState.PADDLES, GameState.ALL]:
            self.good_frame = True
        self.add_text(frame, "%r" % (self.frame_state), (300, 80))
        return results

    def detect_hit(self, objs):
        if self.in_hit_check:
            # If we hit the left paddle
            if self.is_left_hit and np.all((objs[2] > self.hit_position)[:, 0]):
                print("PLAYER 1 HIT")
                self.in_hit_check = False
                self.last_hit_check = -1
                self.is_left_hit = False
                self.hit_position = None
            # If we hit the right paddle
            elif not self.is_left_hit and np.all((objs[2] < self.hit_position)[:, 0]):
                print("PLAYER 2 HIT")
                self.in_hit_check = False
                self.last_hit_check = -1
                self.is_left_hit = False
                self.hit_position = None
            else:
                self.last_hit_check += 1
                if self.last_hit_check > self.hit_max_frames:
                    self.in_hit_check = False
                    self.last_hit_check = -1
                    self.hit_position = None
                    self.is_left_hit = False
                    return
        else:
            # Make sure we're in the ballpark of the left paddle
            if np.absolute(np.subtract(objs[0], objs[2]))[
                :, 0
            ].min() <= self.PADDLE_X_MOE and np.logical_and(
                np.any(objs[2][:, 1] < objs[0][:, 1] + self.PADDLE_Y_MOE),
                np.any(objs[2][:, 1] > objs[0][:, 1] - self.PADDLE_Y_MOE),
            ):
                self.in_hit_check = True
                self.is_left_hit = True
                self.hit_position = objs[2]  # Get ball position
                self.last_hit_check = 0  # 0 frames since we started checking
            # Make sure we're in the ballpark of the right paddle
            elif np.absolute(np.subtract(objs[1], objs[2]))[
                :, 0
            ].min() <= self.PADDLE_X_MOE and np.logical_and(
                np.any(objs[2][:, 1] < objs[1][:, 1] + self.PADDLE_Y_MOE),
                np.any(objs[2][:, 1] > objs[1][:, 1] - self.PADDLE_Y_MOE),
            ):
                self.in_hit_check = True
                self.is_left_hit = False
                self.hit_position = objs[2]
                self.last_hit_check = 0

    def detect_score(self, objs):
        if (
            np.all((objs[2] < objs[0] - self.GOAL_PIXEL_THRESH)[:, 0])
            and self.frame_state == GameState.PADDLES
        ):
            self.p2_score += 1
            print("Player 2 GOAL!")
            print("%s - %s" % (self.p1_score, self.p2_score))
            return True
        elif (
            np.all((objs[2] > objs[1] + self.GOAL_PIXEL_THRESH)[:, 0])
            and self.frame_state == GameState.PADDLES
        ):
            self.p1_score += 1
            print("Player 1 GOAL!")
            print("%s - %s" % (self.p1_score, self.p2_score))
            return True

    def detect_state(self, objs):
        # Detect if out of game
        if self.frame_state == GameState.BALL:
            self.out_of_game_frames += 1
            if (
                self.out_of_game_frames > self.OUT_OF_GAME_MIN_FRAMES
            ):  # If we've been out of game too long
                print("OUT OF GAME!")
        else:
            self.out_of_game_frames = 0  # Or reset counter
        if self.goal_scored and self.frame_state == GameState.PADDLES:
            pass
            # print("WAITING....")
        else:
            if self.goal_scored:
                print("GOAL!")
                self.goal_scored = False
            if self.frame_state == GameState.PADDLES:
                self.last_good_objs[0] = objs[0]
                self.last_good_objs[1] = objs[1]
            else:
                self.last_good_objs = objs

            if self.last_good_objs[self.last_good_objs != 0].size == 24:
                self.detect_hit(self.last_good_objs)

                if self.detect_score(self.last_good_objs):
                    self.goal_scored = True

    def corner_dist(self, obj1, obj2):
        pass

    def handle_input(self):
        key = 0xFF & cv2.waitKey(1)
        if key == ord("q"):
            pass
        elif key == ord("v"):
            cv2.imwrite("test.png", self.treated_frame)
            print("Screenshotted!")
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

    def draw_circles(self, frame, corners, do_draw):
        if do_draw:
            for i in corners:
                x, y = i.ravel()
                print(f"{x}, {y}")
                cv2.circle(frame, (int(x), int(y)), 3, 255, -1)

    def add_text(self, frame, text, pos):
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

    def get_setting(self, setting_name):
        return self.qt_settings.settings[setting_name].slider.value


class GameState(IntEnum):
    NONE = 0
    RIGHT_PADDLE = 1
    LEFT_PADDLE = 2
    PADDLES = 3
    BALL = 4
    BALL_RIGHT_PADDLE = 5
    BALL_LEFT_PADDLE = 6
    ALL = 7
