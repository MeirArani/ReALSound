from gui.manager import CVControls
import sys
from PySide6.QtWidgets import QApplication
from importlib_resources import files
import config
import json

if __name__ == "__main__":
    # Create Qt app
    app = QApplication(sys.argv)
    # create and show the form

    # controls = CVControls()
    # controls.show()

    test = json.loads(files(config).joinpath("cv_settings.json").read_text())
    # run the main loop
    # sys.exit(app.exec())
