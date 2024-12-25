import importlib
from realsound.qt import CVSettingsModel, CVControls
import sys
from PySide6.QtWidgets import QApplication, QListView
from importlib import resources
from realsound import config
import json

if __name__ == "__main__":
    # Create Qt app
    app = QApplication(sys.argv)
    # create and show the form
    view = QListView()

    # controls = CVControls()
    # controls.show()
    model = CVSettingsModel(config_name="cv_settings.json")
    view.setModel(model)
    test = json.loads(resources.read_text(config, "cv_settings.json"))
    print(test)
    for r in range(model.rowCount(0)):
        print(model.index(r).data())
    view.show()
    # run the main loop
    sys.exit(app.exec())
