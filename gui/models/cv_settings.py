from PySide6 import QtCore
from PySide6 import Qt


class CVSettingsModel(QtCore.QAbstractListModel):
    def __init__(self, *args, settings=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings or []

    def data(self, index, role):
        if role == Qt.DisplayRole:
            pass
        return

    def rowCount(self, index):
        return len(self.settings)
