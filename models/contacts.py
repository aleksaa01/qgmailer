from models.base import BaseListModel

from PyQt5.QtCore import Qt

from options import Options


class ContactsListModel(BaseListModel):

    PER_PAGE = Options.app_options['contacts_per_page']

    def __init__(self, data=None, parent=None):
        super().__init__(data, parent)

        Options.optionsChanged.connect(self.change_per_page)

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            return self._displayed_data[index.row()].name

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

    def extractEmail(self, index):
        return self._displayed_data[index.row()].email

    def add_contact(self, contact):
        self.addData([contact, ])

    def add_contacts(self, contacts):
        if not isinstance(contacts, list):
            raise TypeError('contacts must be of type list, got {} instead.'.format(type(contacts)))
        self.addData(contacts)

    def change_per_page(self):
        self.PER_PAGE = Options.app_options['threads_per_page']

        self.begin = 0
        self.end = self.PER_PAGE

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        self.indexesChanged.emit(self.begin, self.end)