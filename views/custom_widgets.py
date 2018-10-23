from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpacerItem, \
    QSizePolicy, QPushButton, QListView, QApplication, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor, QIcon, QPixmap

from GmailApi.email_objects import MessageObject


PagedEmailList_STYLESHEET = '''
    #ThreadLabel{background: "#404040"; color: "white"; padding: 4px;
    margin: 2px; border: 1px solid grey; font-weight: bold; font-size: 14px; border-radius: 10px;}
    #ThreadLabel:hover{background-color: "#31363b"; color: "black"; 
    border: 1px solid red;}
    '''


class PagedEmailList(QWidget):
    """
    :param type:  Current types: personal, social, promotions, updates...
           Type is used to recognize and distinguish widgets.
    :param size:  Size of this widget.
    :param parent: Widget's parent.
    """

    def __init__(self, type, size=tuple(), parent=None):
        super().__init__(parent)

        self.setObjectName('ThreadLabel')

        if not isinstance(size, tuple):
            raise TypeError('Size must be a tuple: (width, height)')

        self.type = type
        self._model = None

        # default size
        if not parent:
            self.width = 900
            self.height = 550

        if size and isinstance(size, tuple):
            self.width = size[0]
            self.height = size[1]
            self.setMinimumSize(size[0], size[1])

        layout = QVBoxLayout()

        self.container = QWidget()
        self.container.setMinimumSize(0, 0)
        self.pagedIndexBox = PagedIndex(self.container)
        layout.addWidget(self.container)

        self.list_view = QListView()
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.list_view)

        self.setLayout(layout)

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        self.list_view.setModel(model)

    def link_email_list(self, f):
        self.list_view.clicked.connect(f)

    def apply_stylesheet(self, stylesheet=None):
        print('Applying stylesheet')
        if stylesheet is None:
            self.setStyleSheet(PagedEmailList_STYLESHEET)
            return
        self.setStyleSheet(stylesheet)

    def link_items(self, f):
        """
        :param f: Function to be called when ListView item is clicked.
        """
        self.list_view.clicked.connect(f)

    def link_navigation(self):
        self.pagedIndexBox.next.clicked.connect(self._model.loadNext)
        self.pagedIndexBox.previous.clicked.connect(self._model.loadPrevious)

    def link_indexes(self):
        self._model.indexesChanged.connect(self.change_indexes)

    def change_indexes(self, begin, end):
        self.pagedIndexBox.indexLabel = '{} - {}'.format(begin, end)
        #self.apply_stylesheet()


class PagedIndex(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.horizontalLayout = QHBoxLayout(parent)
        self.horizontalLayout.setContentsMargins(5, 1, 5, 1)
        self.horizontalLayout.setSpacing(0)

        self._indexLabel = QLabel("0 - 0", parent)
        self.horizontalLayout.addWidget(self._indexLabel)

        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)

        self.previous = QPushButton(parent)
        self.previous.setObjectName('personalPreviousBtn')
        self.previous.setMaximumSize(40, 40)
        self.previous.setCursor(QCursor(Qt.PointingHandCursor))
        self.previous.setText("")
        icon6 = QIcon()
        icon6.addPixmap(QPixmap(":/images/previous_button.png"), QIcon.Normal, QIcon.Off)
        self.previous.setIcon(icon6)
        self.previous.setIconSize(QSize(20, 20))
        self.horizontalLayout.addWidget(self.previous)

        self.next = QPushButton(parent)
        self.next.setObjectName('personalNextBtn')
        self.next.setMaximumSize(40, 40)
        self.next.setCursor(QCursor(Qt.PointingHandCursor))
        self.next.setText("")
        icon7 = QIcon()
        icon7.addPixmap(QPixmap(":/images/next_button.png"), QIcon.Normal, QIcon.Off)
        self.next.setIcon(icon7)
        self.next.setIconSize(QSize(20, 20))
        self.horizontalLayout.addWidget(self.next)

    @property
    def indexLabel(self):
        self._indexLabel.text()

    @indexLabel.setter
    def indexLabel(self, s):
        self._indexLabel.setText(s)


class ResourceNotAssignedError(Exception):
    pass


class EmailViewer(QWebEngineView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.email_page = self.page()
        self.email_page.setHtml('<html><body></body></html>')

        self.res = None
        self.stop_extracting = False
        self._current_messages = []

    def update_content(self, messages):
        if self.res is None:
            raise ResourceNotAssignedError('You have to assign a resource to EmailViewer first.')

        self._current_messages.clear()
        self.email_page.setHtml('<html><body></body></html>')

        for i in range(len(messages)):
            # Give your app a second to process some events
            # and see if user changed the page.
            QApplication.processEvents()

            if self.stop_extracting is True:
                print("STOPPING EXTRACTION...")
                self.stop_extracting = False
                break

            msg_object = MessageObject(messages[i])
            self._append_content(msg_object.raw(self.res))
            self._current_messages.append(msg_object)

    def _append_content(self, email_body):
        self.email_page.runJavaScript('document.write(`{}`);'.format(email_body))

    def assign_resource(self, resource):
        self.res = resource


if __name__ == '__main__':
    # test
    from .icons import icons_rc
    import sys
    app = QApplication(sys.argv)
    b = PagedEmailList('personal', (600, 400))
    b.show()
    app.exec_()
