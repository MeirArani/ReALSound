import PySide6.QtCore
from PongVideo import PongVideo

print(PySide6.__version__)

print(PySide6.QtCore.__version__)

print(vars(PongVideo))

test = PongVideo.PongVideo(
    r"C:\Users\cloud\source\repos\CVPongDemo\PongDemoPy\Pong480.mp4"
)
