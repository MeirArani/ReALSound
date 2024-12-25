import importlib
from realsound.qt import CVControls, CVSettingsListWidget
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
    controls = CVSettingsListWidget(config_name="cv_settings.json")
    controls.show()
    # run the main loop
    sys.exit(app.exec())
