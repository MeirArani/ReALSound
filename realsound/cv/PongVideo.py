import numpy as np
import cv2 as cv


class PongVideoTest:
    MOE = 2
    PADDLE_X_MOE = 18
    PADDLE_Y_MOE = 15
    GOAL_PIXEL_THRESH = 60
    PADDLE_MAX_HEIGHT = 40
    START_FRAME = 0
    PADDLE_MAX_WIDTH = 15
    OUT_OF_GAME_MIN_FRAMES = 2

    def __init__(self, video, settings):
        self.qt_settings = settings
        self.paused = False
        self.good_frame = False
        self.frame_state = 0
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

    def make_slid(
        self,
        a_min: int,
        a_max: int,
        curr: int,
        slider_id: str,
        root_win_name: str,
        on_change_callback=lambda x: x,
    ):
        cv.createTrackbar(slider_id, root_win_name, a_min, a_max, on_change_callback)
        cv.setTrackbarPos(slider_id, root_win_name, curr)
        return slider_id

    def get_UI_slider(self, *ids, root_wind: str):
        """Gets a slider value, used for UI interactions"""
        try:
            results = [cv.getTrackbarPos(idd, root_wind) for idd in ids]
            return results[0] if len(results) == 1 else results
        except Exception as e:
            print(f"Error in getting slider value - {str(e)}")
            return None

    def set_UI_slider(self, id_: str, value: int, root_wind: str):
        cv.setTrackbarPos(id_, root_wind, value)

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

    def detect_objects(self, groups):
        # Four data points: detected, Ball, Paddle1 (left), Paddle2 (right)
        # detected encodes if the next three objects were detected
        # in a single number ranging from 0-7
        # The number is a binary representation of the three objects:
        # All three yield 7 (111) while none yield 0 (000).
        # 6 = Ball + L paddle (110) 5 = Ball + R paddle (101),
        # 4 = Ball (100), 3 = Paddles (011), 2/1 = LP/RP (010/001)
        # The next indexes store the top left corner of the object
        # as well as its width and height
        self.frame_state = 0
        results = np.zeros((3, 4, 2))
        if len(groups) == 0:
            return results
        w = groups[:, 2, 0] - groups[:, 0, 0]
        h = groups[:, 1, 1] - groups[:, 0, 1]
        paddles = groups[np.argwhere(h / w > 2)][:, 0, :]
        paddles = np.take_along_axis(paddles, np.argsort(paddles, axis=1), axis=1)
        ball = groups[np.argwhere(h / w < 2)][:, 0, :]
        if np.any(ball) and len(ball) == 1:
            cv.rectangle(self.frame, ball[0][0], ball[0][3], (255, 0, 0), -1)
            self.frame_state += 4
            results[2] = ball
        if np.any(paddles) and len(paddles) > 0:
            if len(paddles) == 2:
                cv.rectangle(self.frame, paddles[0][0], paddles[0][3], (0, 255, 0), -1)
                cv.rectangle(self.frame, paddles[1][0], paddles[1][3], (0, 255, 0), -1)
                self.frame_state += 3
                if paddles[0][0][0] < self.cap_w / 2:
                    results[0] = paddles[0]
                    results[1] = paddles[1]
                else:
                    results[0] = paddles[1]
                    results[1] = paddles[0]
            elif len(paddles) == 1:
                pass
        # We have paddle movement or paddle and ball movement
        if self.frame_state in [3, 7]:
            self.good_frame = True
        cv.putText(
            self.frame,
            "%r" % (self.frame_state),
            (300, 80),
            cv.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )
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
            and self.frame_state == 3
        ):
            self.p2_score += 1
            print("Player 2 GOAL!")
            print("%s - %s" % (self.p1_score, self.p2_score))
            return True
        elif (
            np.all((objs[2] > objs[1] + self.GOAL_PIXEL_THRESH)[:, 0])
            and self.frame_state == 3
        ):
            self.p1_score += 1
            print("Player 1 GOAL!")
            print("%s - %s" % (self.p1_score, self.p2_score))
            return True

    def detect_state(self, objs):
        pass

    def corner_dist(self, obj1, obj2):
        pass

    def start(self, window_name="Pong Demo"):
        show_circles = False

        cap = cv.VideoCapture(self.video)
        print(cap)
        cap.set(cv.CAP_PROP_POS_FRAMES, self.START_FRAME)

        self.cap_w = cap.get(cv.CAP_PROP_FRAME_WIDTH)
        self.cap_h = cap.get(cv.CAP_PROP_FRAME_HEIGHT)

        self.VERT_MAX = self.PADDLE_MAX_HEIGHT / self.cap_h
        self.HORZ_MAX = self.PADDLE_MAX_WIDTH / self.cap_w

        cv.namedWindow(window_name)

        tracker = cv.TrackerMIL.create()

        self.make_slid(0, 100, 2, "threshold", window_name)
        self.make_slid(1, 5, 2, "blocksize", window_name)
        self.make_slid(1, 4, 3, "ksize", window_name)
        self.make_slid(3, 6, 4, "k", window_name)
        self.make_slid(1, 25, 12, "numPoints", window_name)
        self.make_slid(1, 20, 3, "minDistance", window_name)

        last_good_objs = np.zeros((3, 4, 2), np.int64)

        if not cap.isOpened():
            print("Cannot open camera")
            exit()
        while True:
            # capture, frame by frame (sick guitar riff)
            ret, self.frame = cap.read()
            cv.putText(
                self.frame,
                "%r" % (cap.get(cv.CAP_PROP_POS_FRAMES)),
                (450, 80),
                cv.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )
            self.good_frame = False

            self.threshold = (
                # self.get_UI_slider("threshold", root_wind=window_name) / 100
                self.qt_settings.settings["thresh"].slider.value
                / 100
            )

            if not ret:
                print("Frame is fucked")
                break
            gray = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
            corners = cv.goodFeaturesToTrack(
                gray,
                # self.get_UI_slider("numPoints", root_wind=window_name),
                # self.get_UI_slider("threshold", root_wind=window_name) / 1000,
                # self.get_UI_slider("minDistance", root_wind=window_name),
                self.qt_settings.settings["points"].slider.value,
                self.qt_settings.settings["thresh"].slider.value / 1000,
                self.qt_settings.settings["distance"].slider.value,
            )
            groups = self.group_points(corners)
            objs = self.detect_objects(groups)
            if self.frame_state == 4:
                self.out_of_game_frames += 1
                if self.out_of_game_frames > self.OUT_OF_GAME_MIN_FRAMES:
                    print("OUT OF GAME!")
            else:
                self.out_of_game_frames = 0
            if self.goal_scored and self.frame_state == 3:
                pass
                # print("WAITING....")
            else:
                if self.goal_scored:
                    print("GO!")
                    self.goal_scored = False
                if self.frame_state == 3:
                    self.last_good_objs[0] = objs[0]
                    self.last_good_objs[1] = objs[1]
                else:
                    self.last_good_objs = objs

                if self.last_good_objs[self.last_good_objs != 0].size == 24:
                    self.detect_hit(last_good_objs)

                    if self.detect_score(self.last_good_objs):
                        self.goal_scored = True
            if show_circles:
                for i in corners:
                    x, y = i.ravel()
                    cv.circle(self.frame, (x, y), 3, 255, -1)
            cv.imshow("Frame testing", self.frame)
            print(np.shape(self.frame))
            if not self.good_frame:
                pass
                # bad_frames.append(cap.get(cv.CAP_PROP_POS_FRAMES))
                # print(cap.get(cv.CAP_PROP_POS_FRAMES))

            key = 0xFF & cv.waitKey(1)

            if key == ord("q"):
                break
            elif key == ord("v"):
                cv.imwrite("test.png", gray)
                print("Screenshotted!")
            elif key == ord("p"):
                self.paused = not self.paused
            elif key == ord("c"):
                show_circles = not show_circles
            while self.paused:
                key = 0xFF & cv.waitKey(1)
                if key == ord("s"):
                    break
                elif key == ord("p"):
                    self.paused = not self.paused
                elif key == ord("c"):
                    show_circles = not show_circles
        cap.release()
        print(self.bad_frames)
        cv.destroyAllWindows()
