from PyQt5.QtCore import QAbstractListModel, Qt, pyqtSignal

from options import Options


class ContactsListModel(QAbstractListModel):

    PER_PAGE = Options.app_options['contacts_per_page']
    indexesChanged = pyqtSignal(int, int)

    def __init__(self, data=None, parent=None):
        super().__init__(parent)

        Options.optionsChanged.connect(self.change_per_page)

        self._data = data if data else []
        self.begin = 0
        self.end = self.PER_PAGE
        self._displayed_data = self._data[self.begin:self.end]

    def rowCount(self, parent=None):
        return len(self._displayed_data)

    def displayedIndex(self):
        # this method might be useful for pagination and it would
        # be more useful outisde of this model.
        return self.begin, self.end

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            return self._displayed_data[index.row()]

        elif role == Qt.DecorationRole:
            # return pixmap of first letter of Person's name
            pass

        elif role == Qt.ToolTipRole:
            pass


    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def insertRows(self, position, rows, parent=None):
        pass

    def removeRows(self, position, rows, parent=None):
        pass

    def createData(self, data):
        # Use only if no widgets are connected to this model,
        # if you have connected widgets use "addData" instead.
        self._data = data
        self._displayed_data = self._data[self.begin:self.end]

    def addData(self, data):
        # Adds data to already existing data, so model reset is required.
        self.beginResetModel()
        self._data = data + self._data
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
        self.begin += self.PER_PAGE
        self.end += self.PER_PAGE
        if self.begin > len(self._data) - self.PER_PAGE:
            if self.end >= len(self._data) and self.begin < len(self._data):
                self.begin = self.begin
            elif self.end >= len(self._data) and self.begin >= len(self._data):
                self.begin -= self.PER_PAGE
            else:
                self.begin = len(self._data) - self.PER_PAGE
        if self.end > len(self._data):
            self.end = len(self._data)

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self.indexesChanged.emit(self.begin, self.end)

    def loadPrevious(self):
        self.end = self.begin
        if self.end < self.PER_PAGE:
            if len(self._data) >= self.PER_PAGE:
                self.end = self.PER_PAGE
            else:
                self.end = len(self._data)

        self.begin -= self.PER_PAGE
        if self.begin < 0:
            self.begin = 0

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self.indexesChanged.emit(self.begin, self.end)

    def change_per_page(self):
        self.PER_PAGE = Options.app_options['contacts_per_page']

        self.begin = 0
        self.end = self.PER_PAGE

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self.indexesChanged.emit(self.begin, self.end)
