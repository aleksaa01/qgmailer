from models.base import BaseListModel

from PyQt5.QtCore import Qt

from options import Options


class ThreadsListModel(BaseListModel):

    def __init__(self, data=None, parent=None):
        super().__init__(data, parent)

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            return self._displayed_data[index.row()].snippet

        elif role == Qt.DecorationRole:
            pass

        elif role == Qt.ToolTipRole:
            pass

    def extractId(self, index):
        return self._displayed_data[index.row()].id

    def change_per_page(self):
        self.begin = 0
        self.end = self.per_page

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self.indexesChanged.emit(self.begin, self.end)

    def set_per_page(self, per_page):
        self.per_page = per_page
