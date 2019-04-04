from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog, QStackedWidget, \
    QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSize, QRect
from views.custom_widgets import PagedList
from experiment import ThreadsViewModel



class AppView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('QGmailer')
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        self.resize(640, 480)

        # cw - central widget
        self.cw = QWidget(self)
        self.cw.setFixedSize(640, 480)

        self.switcher = QStackedWidget(self.cw)
        self.pages = []

        self.inbox_page = InboxPage(self.cw)
        self.add_page(self.inbox_page)
        self.sendemail_page = SendEmailPage(self.cw)
        self.add_page(self.sendemail_page)
        self.sent_page = SentPage(self.cw)
        self.add_page(self.sent_page)
        self.contacts_page = ContactsPage(self.cw)
        self.add_page(self.contacts_page)
        self.trash_page = TrashPage(self.cw)
        self.add_page(self.trash_page)
        self.options_dialog = OptionsDialog(self.cw)

        self.sidebar = SidebarNavigation(self.switcher, self.pages, self.cw)
        self.sidebar.setFixedSize(50, 480)

        layout = QVBoxLayout()
        layout.addWidget(self.switcher)
        self.cw.setLayout(layout)
        self.setCentralWidget(self.cw)
        self.show()

    def add_page(self, page):
        self.pages.append(page)
        self.switcher.addWidget(page)


class Page(QWidget):
    """Base class for all Pages."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon = None
        self._index = 0

    def navigation_icon(self):
        raise NotImplementedError('Classes that inherit from Page have to implement navigation_icon method.')

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        # Do something else.
        self._index = index


class InboxPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.paged_list = PagedList(size=(200, 200))
        self.vm = ThreadsViewModel()
        self.paged_list.model = self.vm.threads_listmodel
        self.okbtn = QPushButton('OK')
        self.okbtn.clicked.connect(self.vm.handle_ok)
        self.cancelbtn = QPushButton('Cancel')
        self.cancelbtn.clicked.connect(self.vm.handle_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.paged_list)
        layout.addWidget(self.okbtn)
        layout.addWidget(self.cancelbtn)
        self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/inbox_icon.png'))
        return self.icon


class ContactsPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.paged_list = PagedList(size=(200, 200))
        self.vm = ThreadsViewModel()
        self.paged_list.model = self.vm.threads_listmodel
        self.okbtn = QPushButton('OK')
        self.okbtn.clicked.connect(self.vm.handle_ok)
        self.cancelbtn = QPushButton('Cancel')
        self.cancelbtn.clicked.connect(self.vm.handle_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.paged_list)
        layout.addWidget(self.okbtn)
        layout.addWidget(self.cancelbtn)
        self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/contacts_icon2.png'))
        return self.icon


class SentPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.paged_list = PagedList(size=(200, 200))
        self.vm = ThreadsViewModel()
        self.paged_list.model = self.vm.threads_listmodel
        self.okbtn = QPushButton('OK')
        self.okbtn.clicked.connect(self.vm.handle_ok)
        self.cancelbtn = QPushButton('Cancel')
        self.cancelbtn.clicked.connect(self.vm.handle_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.paged_list)
        layout.addWidget(self.okbtn)
        layout.addWidget(self.cancelbtn)
        self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/sent_icon.png'))
        return self.icon


class SendEmailPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.paged_list = PagedList(size=(200, 200))
        self.vm = ThreadsViewModel()
        self.paged_list.model = self.vm.threads_listmodel
        self.okbtn = QPushButton('OK')
        self.okbtn.clicked.connect(self.vm.handle_ok)
        self.cancelbtn = QPushButton('Cancel')
        self.cancelbtn.clicked.connect(self.vm.handle_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.paged_list)
        layout.addWidget(self.okbtn)
        layout.addWidget(self.cancelbtn)
        self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/send_icon.png'))
        return self.icon


class TrashPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.paged_list = PagedList(size=(200, 200))
        self.vm = ThreadsViewModel()
        self.paged_list.model = self.vm.threads_listmodel
        self.okbtn = QPushButton('OK')
        self.okbtn.clicked.connect(self.vm.handle_ok)
        self.cancelbtn = QPushButton('Cancel')
        self.cancelbtn.clicked.connect(self.vm.handle_cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.paged_list)
        layout.addWidget(self.okbtn)
        layout.addWidget(self.cancelbtn)
        self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/trash_icon.png'))
        return self.icon


class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)


class SidebarNavigation(QWidget):
    """
    :param switcher: Some sort of object or widget that can switch between the pages.
    Like QStackedWidget for example, or it can be some custom widget with predefined interface.
    :param pages: List of all pages(InboxPage, SendEmailPage, TrashPage)

    Think about how would you implement this. Because you can have a page itself contain
    an icon for representation(Like navigation_icon, as attribute of the class).
    And you could make it so positions of icons get displayed dynamically and not in particular order.
    """
    def __init__(self, switcher, pages, parent=None):
        super().__init__(parent)

        self.switcher = switcher
        self.pages = pages


        layout = QVBoxLayout()
        self.btns = []
        # connector = lambda i: lambda: self.check(i)
        # page = pages[0]
        # page.index = -1
        for count, page in enumerate(pages):
            page.index = count
            btn = QPushButton()
            btn.setIcon(page.navigation_icon())
            btn.setIconSize(QSize(40, 40))
            btn.clicked.connect(self.bind_switch(page))
            self.btns.append(btn)
            layout.addWidget(btn)

        self.setLayout(layout)

    def bind_switch(self, page):
        return lambda: self.switcher.setCurrentIndex(page.index)



from views.icons import icons_rc