from PyQt5.QtCore import QAbstractListModel, Qt, pyqtSignal


class BaseListModel(QAbstractListModel):

    indexesChanged = pyqtSignal(int, int)

    def __init__(self, data=None, parent=None):
        super().__init__(parent)

        self._data = data if data else []
        self.begin = 0
        self.end = 0
        self._displayed_data = self._data[self.begin:self.end]

        self.per_page = 0

    def rowCount(self, parent=None):
        return len(self._displayed_data)

    def displayedIndex(self):
        # this method might be useful for pagination and it would
        # be more useful outisde of this model.
        return self.begin, self.end

    def data(self, index, role=None):
        raise NotImplementedError('data method is not implemented yet.')

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def createData(self, data):
        # Use only if no widgets are connected to this model,
        # if you have connected widgets use "addData" instead.
        self._data = data
        self._displayed_data = self._data[self.begin:self.end]

    def addData(self, data):
        # Adds data to already existing data, so model reset is required.
        self.beginResetModel()
        self._data = self._data + data
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()
        self.indexesChanged.emit(self.begin, self.end)

    def replaceData(self, data):
        self.beginResetModel()
        self._data = data
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()
        self.indexesChanged.emit(self.begin, self.end)

    def checkData(self):
        if self._data:
            return True
        return False

    def loadNext(self):
        self.begin += self.per_page
        self.end += self.per_page
        if self.begin > len(self._data) - self.per_page:
            if self.end >= len(self._data) and self.begin < len(self._data):
                self.begin = self.begin
            elif self.end >= len(self._data) and self.begin >= len(self._data):
                self.begin -= self.per_page
            else:
                self.begin = len(self._data) - self.per_page
        if self.end > len(self._data):
            self.end = len(self._data)

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self.indexesChanged.emit(self.begin, self.end)

    def loadPrevious(self):
        self.end = self.begin
        if self.end < self.per_page:
            if len(self._data) >= self.per_page:
                self.end = self.per_page
            else:
                self.end = len(self._data)

        self.begin -= self.per_page
        if self.begin < 0:
            self.begin = 0

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self.indexesChanged.emit(self.begin, self.end)

    def removeData(self, index):
        self._data.pop(index.row())
        self.end = max(self.begin, self.end - 1)

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self.indexesChanged.emit(self.begin, self.end)