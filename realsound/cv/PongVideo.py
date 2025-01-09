from enum import IntEnum
import time
import numpy as np
import cv2

from PySide6.QtCore import Slot, Signal, QObject


class GameState(IntEnum):
    ATTRACT = 0
    RIGHT_PADDLE = 1
    LEFT_PADDLE = 2
    MISSING_BALL = 3
    MISSING_PADDLES = 4
    BALL_RIGHT_PADDLE = 5
    BALL_LEFT_PADDLE = 6
    IN_GAME = 7
    LEFT_GOAL = 8
    RIGHT_GOAL = 9
    BREAK = 10


class PongVideoTest(QObject):
    MOE = 2
    PADDLE_X_MOE = 18
    PADDLE_Y_MOE = 15
    GOAL_PIXEL_THRESH = 60
    PADDLE_MAX_HEIGHT = 40
    START_FRAME = 0
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

    # GOAL
    sound_event_goal_scored = Signal(GameState)

    def __init__(self, video, settings, parent=None):
        super().__init__(parent)
        self.qt_settings = settings
        self.paused = False
        self.good_frame = False
        self.frame_state = GameState.ATTRACT
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
        self.show_circles = False

        self.on_break = False
        self.cap = None
        self.running = False
        self.starting_frame = False
        self.is_back_from_break = False

        self.prev_time = 0

        self.last_centers = None

    def start(self, window_name="Pong Demo"):

        # Init values
        self.running = True
        self.starting_frame = True
        show_circles = False

        # Init capture
        self.cap = cv2.VideoCapture(self.video)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.START_FRAME)

        # Init Width/Height
        self.cap_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.cap_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.VERT_MAX = self.PADDLE_MAX_HEIGHT / self.cap_h
        self.HORZ_MAX = self.PADDLE_MAX_WIDTH / self.cap_w

        self.last_good_objs = np.zeros((3, 4, 2), np.int64)

        if not self.cap.isOpened():
            print("Cannot open camera")
            exit()

        while self.running:

            time_elapsed = time.time() - self.prev_time

            if time_elapsed > 1 / self.FRAME_RATE:
                if self.starting_frame:
                    self.starting_frame = False
                self.run_frame(self.cap)
                self.prev_time = time.time()

            # cv2.waitKey(0)

            # capture, frame by frame (sick guitar riff)

        self.cap.release()
        cv2.destroyAllWindows()

    def run_frame(self, cap):
        if self.is_back_from_break:
            self.is_back_from_break = False
        ret, frame = self.cap.read()

        self.add_text(frame, "%r" % (self.cap.get(cv2.CAP_PROP_POS_FRAMES)), (450, 80))

        self.good_frame = False

        self.threshold = (
            # self.get_UI_slider("threshold", root_wind=window_name) / 100
            self.qt_settings.settings["thresh"].slider.value
            / 100
        )

        if not ret:
            print("Frame is fucked")
            self.running = False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners = cv2.goodFeaturesToTrack(
            gray,
            # self.get_UI_slider("numPoints", root_wind=window_name),
            # self.get_UI_slider("threshold", root_wind=window_name) / 1000,
            # self.get_UI_slider("minDistance", root_wind=window_name),
            self.qt_settings.settings["points"].slider.value,
            self.qt_settings.settings["thresh"].slider.value / 1000,
            self.qt_settings.settings["distance"].slider.value,
        )

        groups = self.group_points(corners)
        objs, centers = self.detect_state(frame, groups)

        if self.frame_state == GameState.MISSING_PADDLES:
            self.out_of_game_frames += 1
            if self.out_of_game_frames > self.OUT_OF_GAME_MIN_FRAMES:
                self.frame_state = GameState.ATTRACT
        else:
            self.out_of_game_frames = 0
        if self.frame_state == GameState.MISSING_BALL:
            print(f"{self.p1_score}, {self.p2_score}")
            # self.frame_state = GameState.LEFT_GOAL
        else:
            if self.goal_scored:
                print("GOAL!")
                self.goal_scored = False

            # Check if this is a good frame
            if self.frame_state == GameState.MISSING_BALL:
                self.last_good_objs[0] = objs[0]
                self.last_good_objs[1] = objs[1]
            else:
                self.last_good_objs = objs

            # If we need to detect a hit
            if self.last_good_objs[self.last_good_objs != 0].size == 24:
                self.detect_hit(self.last_good_objs)

                if self.detect_score(self.last_good_objs):
                    self.goal_scored = True

        if self.show_circles:
            show_circles(frame, corners)

        self.add_text(frame, "%r" % (GameState(self.frame_state).name), (250, 80), 0.8)

        self.game_data_update(centers)
        self.process_audio(centers)

        cv2.imshow("Frame testing", cv2.resize(frame, (1920, 1080)))
        if not self.good_frame:
            pass

        key = 0xFF & cv2.waitKey(1)

        if key == ord("q"):
            self.running = False
        elif key == ord("v"):
            cv2.imwrite("test.png", gray)
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

    def on_frame_update(self):
        pass

    @Slot()
    def stop(self):
        print("EXITED!")
        self.running = False

    def get_centers(self):
        pass

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

    def show_circles(self, frame, corners):
        for i in corners:
            x, y = i.ravel()
            cv2.circle(frame, (x, y), 3, 255, -1)

    def make_slid(
        self,
        a_min: int,
        a_max: int,
        curr: int,
        slider_id: str,
        root_win_name: str,
        on_change_callback=lambda x: x,
    ):
        cv2.createTrackbar(slider_id, root_win_name, a_min, a_max, on_change_callback)
        cv2.setTrackbarPos(slider_id, root_win_name, curr)
        return slider_id

    def get_UI_slider(self, *ids, root_wind: str):
        """Gets a slider value, used for UI interactions"""
        try:
            results = [cv2.getTrackbarPos(idd, root_wind) for idd in ids]
            return results[0] if len(results) == 1 else results
        except Exception as e:
            print(f"Error in getting slider value - {str(e)}")
            return None

    def set_UI_slider(self, id_: str, value: int, root_wind: str):
        cv2.setTrackbarPos(id_, root_wind, value)

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
                horz_rt = (maxes[0] - mins[0]) / self.cap_w
                vert_rt = (maxes[1] - mins[1]) / self.cap_h  # Same for height
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

    # TODO: FIX STATE MESS!!!!
    def detect_state(self, frame, groups):
        # Four data points: detected, Ball, Paddle1 (left), Paddle2 (right)
        # detected encodes if the next three objects were detected
        # in a single number ranging from 0-7
        # The number is a binary representation of the three objects:
        # All three yield 7 (111) while none yield 0 (000).
        # 6 = Ball + L paddle (110) 5 = Ball + R paddle (101),
        # 4 = Ball (100), 3 = Paddles (011), 2/1 = LP/RP (010/001)
        # The next indexes store the top left corner of the object
        # as well as its width and height

        if len(groups) == 0:
            return np.zeros((3, 4, 2))

        w = groups[:, 2, 0] - groups[:, 0, 0]
        h = groups[:, 1, 1] - groups[:, 0, 1]

        ball = groups[np.argwhere(h / w < 2)]
        has_ball = np.any(ball) and len(ball) == 1

        paddles = groups[np.argwhere(h / w > 2)][:, 0, :]
        paddles = np.take_along_axis(paddles, np.argsort(paddles, axis=1), axis=1)
        has_paddles = (np.any(paddles) and len(paddles) > 0) and len(paddles) == 2

        results = np.zeros((3, 4, 2))
        centers = np.zeros((3, 2))

        if self.frame_state is GameState.BREAK:
            self.last_centers = None

        if has_ball:
            if self.frame_state is GameState.BREAK:
                self.back_from_break()

            self.frame_state = GameState.ATTRACT

            ball = ball.reshape((4, 2))

            cv2.rectangle(frame, ball[0], ball[3], (255, 0, 0), -1)
            self.frame_state += GameState.MISSING_PADDLES
            results[2] = ball
            centers[2] = (ball[0] + ball[2]) / 2

        if self.frame_state is GameState.ATTRACT and has_paddles:
            self.on_break = True

        if (
            self.frame_state is not GameState.ATTRACT
            and not self.on_break
            and has_paddles
        ):
            if not has_ball:
                self.frame_state = GameState.ATTRACT
            paddles = paddles.reshape(2, 4, 2)

            # Draw Rectangles
            cv2.rectangle(frame, paddles[0][0], paddles[0][3], (0, 255, 0), -1)
            cv2.rectangle(frame, paddles[1][0], paddles[1][3], (0, 255, 0), -1)
            self.frame_state += GameState.MISSING_BALL
            # Order paddles by direction (left first)
            if paddles[0][0][0] < self.cap_w / 2:
                results[0] = paddles[0]
                results[1] = paddles[1]
            else:
                results[0] = paddles[1]
                results[1] = paddles[0]

            # Calc rectangle centers
            centers[0] = (results[0][0] + results[0][3]) / 2
            centers[1] = (results[1][0] + results[1][3]) / 2

        # We have paddle movement or paddle and ball movement
        if self.frame_state in [GameState.MISSING_BALL, GameState.IN_GAME]:
            self.good_frame = True

        # If this is our first calc
        if self.last_centers is None:
            self.last_centers = centers

        if not self.on_break and self.frame_state is not GameState.ATTRACT:
            deltas = np.sum(np.abs(centers - self.last_centers), axis=1)
            for i, delta in enumerate(deltas):
                if delta > self.MAX_DELTA:
                    print(
                        f"BAD DELTA FOUND! Corrected object {i} from {centers[i]} to previous #position {self.last_centers[i]}"
                    )
                    centers[i] = self.last_centers[i]
            self.last_centers = centers
        return results, centers

    def detect_hit(self, objs):
        if self.in_hit_check:
            # If we hit the left paddle
            if self.is_left_hit and np.all((objs[2] > self.hit_position)[:, 0]):
                print("PLAYER 1 HIT")
                self.in_hit_check = False
                self.last_hit_check = -1
                self.is_left_hit = False
                self.send_hit_sound(True)
                self.hit_position = None
            # If we hit the right paddle
            elif not self.is_left_hit and np.all((objs[2] < self.hit_position)[:, 0]):
                print("PLAYER 2 HIT")
                self.in_hit_check = False
                self.last_hit_check = -1
                self.is_left_hit = False
                self.send_hit_sound(False)
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
            and self.frame_state == GameState.MISSING_BALL
        ):
            self.p2_score += 1
            print("Player 2 GOAL!")
            print("%s - %s" % (self.p1_score, self.p2_score))
            self.frame_state = GameState.RIGHT_GOAL
            self.on_break = True
            self.send_goal_sound(GameState.RIGHT_GOAL)
            return True
        elif (
            np.all((objs[2] > objs[1] + self.GOAL_PIXEL_THRESH)[:, 0])
            and self.frame_state == GameState.MISSING_BALL
        ):
            self.p1_score += 1
            print("Player 1 GOAL!")
            print("%s - %s" % (self.p1_score, self.p2_score))
            self.frame_state = GameState.LEFT_GOAL
            self.on_break = True
            self.send_goal_sound(GameState.LEFT_GOAL)
            return True

    def game_data_update(self, centers):
        self.cv_event_frame_updated.emit(centers, self.frame_state)

    def process_audio(self, centers):
        match self.frame_state:
            case GameState.IN_GAME:
                self.update_audio_position(centers)
                pass
            case GameState.ATTRACT:
                pass
            case _:
                pass

    def back_from_break(self):
        self.on_break = False
        self.toggle_ball_sound(True)
        self.is_back_from_break = True

    def update_audio_position(self, centers):
        dx = (centers[2][0] - centers[0][0]) / (self.cap_w * 0.725)
        dy = (centers[2][1] - centers[0][1]) / self.cap_h
        self.sound_event_ball_moved.emit(dx, dy)

    def toggle_ball_sound(self, toggle):
        self.sound_event_ball_toggle.emit(toggle)

    def send_goal_sound(self, player):
        self.toggle_ball_sound(False)
        self.sound_event_goal_scored.emit(player)
        pass

    def send_hit_sound(self, playerOneHit):
        self.sound_event_ball_hit.emit(playerOneHit)
