from PySide6.QtWidgets import QWidget, QGridLayout
from PySide6.QtCore import Slot, Signal
from numpy import ndarray
import cv2
from sys import maxsize

from realsound.core import VisionLayer, DecisionLayer, AudificationLayer
from realsound.cv import VideoWidget


class RealSound(QWidget):

    # How many frames we display transient state info
    SHOW_TIME = 120

    frame_finished = Signal(ndarray)

    def __init__(self, start_frame=0, parent=None):
        super().__init__(parent)

        self.audification = AudificationLayer(self)
        self.vision = VisionLayer(self)
        self.decision = DecisionLayer(self)

        # Vars
        self._frame = None
        self._frame_count = start_frame

        # UI
        self.video_out = VideoWidget(self)
        _layout = QGridLayout(self)
        _layout.addWidget(self.video_out, 0, 0)

        # Events
        self.decision.p1.on_hit.connect(self.on_hit)
        self.decision.p2.on_hit.connect(self.on_hit)
        self.decision.ball.on_ricochet.connect(self.on_ricochet)

        self.frame_finished.connect(self.video_out.display)

    @Slot(ndarray)
    def on_new_frame(self, frame):
        self._frame_count += 1
        self._frame = frame

        self._entities = self.vision.see(self.frame)

        self._audio_objs = self.decision.decide(self._entities)

        self.audification.playback(self._audio_objs)

        self.display_frame_count()
        self.display_state()
        self.display_score()

        self.frame_finished.emit(frame)

    @property
    def frame(self):
        return self._frame

    def add_text(self, text, pos, scale=1):
        self._frame = cv2.putText(
            self.frame,
            text,
            pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2,
        )

    def display_frame_count(self):
        self.add_text("%r" % (self._frame_count), (450, 80))

    def display_state(self):
        self.add_text("%r" % (self.decision.state), (290, 50), 0.8)

    def display_score(self):
        self.add_text(
            f"{self.decision.p1.score} - {self.decision.p2.score}",
            (290, 400),
        )

    @Slot(str)
    def on_hit(self, paddle):
        print(f"{paddle} hit!")

    def on_ricochet(self):
        print("RICOCHET!")

    def show_circles(frame, corners):
        for i in corners:
            x, y = i.ravel()
            cv2.circle(frame, (x, y), 3, 255, -1)
