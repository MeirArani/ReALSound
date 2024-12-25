from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListView
import json
from importlib import resources
from realsound import config


class CVSettingsListWidget(QListView):
    def __init__(self, parent=...):
        super().__init__(parent)
        self.model = CVSettingsModel("cv_settings.json")
        self.setModel(self.model)

    def build_settings(self):
        for r in range(self.model.rowCount(0)):
            data = self.model().index(r)
            pass
        pass


class CVSettingsModel(QtCore.QAbstractListModel):
    def __init__(self, *args, config_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = json.loads(
            resources.read_text(config, config_name)
        ) or json.loads(resources.read_text(config, "cv_settings.json").read_text())

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # return list(self.settings)[0]
            return self.get_key(index.row())
        return

    def rowCount(self, index):
        return len(self.settings)

    def get_key(self, n=0):
        if n < 0:
            n += len(self.settings)
        for i, key in enumerate(self.settings.keys()):
            if i == n:
                return key
        raise IndexError("dictionary index out of range")

    def get_val(self, n=0):
        if n < 0:
            n += len(self.settings)
        for i, val in enumerate(self.settings.values()):
            if i == n:
                return val
        raise IndexError("dictionary index out of range")
