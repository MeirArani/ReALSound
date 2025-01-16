import importlib
from realsound.qt import CVSettingsListWidget
from realsound.cv import VisionLayer
import sys
from PySide6.QtWidgets import QApplication, QListView
from importlib import resources
from realsound import config
import json

if __name__ == "__main__":
    # Create Qt app
    app = QApplication(sys.argv)
    # create and show the form

    # controls = CVControls()
    # controls.show()
    controls = CVSettingsListWidget(default_config="cv_settings.json")
    video = VisionLayer(
        r"C:\Users\cloud\source\repos\CVPongDemo\PongDemoPy\Pong480.mp4", controls
    )
    controls.show()
    video.start()
    # run the main loop
    sys.exit(app.exec())
