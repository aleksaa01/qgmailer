from PyQt5.QtCore import QAbstractListModel, Qt


# Maybe add "id" attribute for more easier distinction between multiple similar models.
# Like "personal threads model", "social threads model"... Because you have one general
# class (ThreadsListModel), you need to be able to identify created models somehow.
class ThreadsListModel(QAbstractListModel):

    PER_PAGE = 50

    def __init__(self, data=None, parent=None):
        super().__init__(parent)

        self._data = data if data else []
        self.begin = 0
        self.end = self.PER_PAGE
        self._displayed_data = self._data[self.begin:self.end]

    def rowCount(self, parent=None):
        return len(self._displayed_data)

    def displayedRowCount(self):
        # this method might be useful for pagination and it would
        # be more useful outisde of this model.
        return len(self._displayed_data)

    def data(self, QModelIndex, role=None):

        if role == Qt.ToolTipRole:
            pass

        elif role == Qt.DecorationRole:
            pass

        elif role == Qt.DisplayRole:
            pass

    def flags(self, QModelIndex):
        pass

    def insertRows(self, position, rows, parent=None):
        pass

    def removeRows(self, position, rows, parent=None):
        pass

    def createData(self, data):
        # Use only if no widgets are connected to this model,
        # if you have connected widgets use "addData" instead.
        pass

    def addData(self, data):
        # Adds data to already existing data, so model reset is required.
        pass

    def checkData(self):
        if self._data:
            return True
        return False

    def loadNext(self):
        pass

    def loadPrevious(self):
        pass
