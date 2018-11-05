from PyQt5.QtCore import QAbstractListModel, Qt, pyqtSignal

from options import Options


# Maybe add "id" attribute for more easier distinction between multiple similar models.
# Like "personal threads model", "social threads model"... Because you have one general
# class (ThreadsListModel), you need to be able to identify created models somehow.
class ThreadsListModel(QAbstractListModel):

    PER_PAGE = Options.extract_option('threads_per_page')
    indexesChanged = pyqtSignal(int, int)

    def __init__(self, data=None, parent=None):
        super().__init__(parent)

        self._data = data if data else []
        self.begin = 0
        self.end = self.PER_PAGE
        self._displayed_data = self._data[self.begin:self.end]

        #self.filepath = path.join(path.dirname(__file__), 'circle.png')

    def rowCount(self, parent=None):
        return len(self._displayed_data)

    def displayedIndex(self):
        # this method might be useful for pagination and it would
        # be more useful outisde of this model.
        return self.begin, self.end

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            return self._displayed_data[index.row()].snippet

        elif role == Qt.DecorationRole:
            # pix = QPixmap(self.filepath)
            # painter = QPainter(pix)
            # font = QFont('Arial')
            # font.setPixelSize(12)
            # painter.setFont(font)
            #
            # snippet = self._displayed_data[index.row()].snippet
            # if snippet:
            #     painter.drawText(QPoint(12, 20), snippet[0].upper())
            # else:
            #     painter.drawText(QPoint(12, 20), ' ')
            # return pix
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

    def extractId(self, index):
        return self._displayed_data[index.row()].id

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
        #print(self.begin, self.end)

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
        #print(self.begin, self.end)

        self.indexesChanged.emit(self.begin, self.end)

    def pageLength(self):
        return len(self._displayed_data)
