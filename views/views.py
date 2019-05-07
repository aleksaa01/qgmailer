from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog, QStackedWidget, \
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSize, QRect
from views.custom_widgets import PagedList
from experiment import MessagesViewModel, ContactsViewModel



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

        self.inbox_page = InboxPage(self.switcher)
        self.add_page(self.inbox_page)
        self.sendemail_page = SendEmailPage(self.switcher)
        self.add_page(self.sendemail_page)
        self.sent_page = SentPage(self.switcher)
        self.add_page(self.sent_page)
        self.contacts_page = ContactsPage(self.switcher)
        self.add_page(self.contacts_page)
        self.trash_page = TrashPage(self.switcher)
        self.add_page(self.trash_page)
        self.options_dialog = OptionsDialog(self.switcher)

        self.sidebar = SidebarNavigation(self.switcher, self.pages, self.cw)
        self.sidebar.setFixedSize(50, 480)

        layout = QHBoxLayout()
        layout.addWidget(self.sidebar)
        layout.addWidget(self.switcher)
        self.cw.setLayout(layout)
        self.setCentralWidget(self.cw)
        self.show()

    def add_page(self, page):
        self.pages.append(page)
        self.switcher.addWidget(page)

    def load(self):
        for page in self.pages:
            page.execute_viewmodels()


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

    def execute_viewmodels(self):
        raise NotImplementedError('Classes that inherit from Page have to implement execute_viewmodels method.')


class InboxPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_personal = QWidget()
        self.list_personal = PagedList(None, (200, 200), self.tab_personal)
        self.vm_personal = MessagesViewModel('personal')
        self.list_personal.model = self.vm_personal.threads_listmodel
        self._bind_list_page_switch(self.list_personal, self.vm_personal)
        self.tab_social = QWidget()
        self.list_social = PagedList(None, (200, 200), self.tab_social)
        self.vm_social = MessagesViewModel('social')
        self.list_social.model = self.vm_social.threads_listmodel
        self.tab_promotions = QWidget()
        self.list_promotions = PagedList(None, (200, 200), self.tab_promotions)
        self.vm_promotions = MessagesViewModel('promotions')
        self.list_promotions.model = self.vm_promotions.threads_listmodel
        self.tab_updates = QWidget()
        self.list_updates = PagedList(None, (200, 200), self.tab_updates)
        self.vm_updates = MessagesViewModel('updates')
        self.list_updates.model = self.vm_updates.threads_listmodel

        self.tab_widget.addTab(self.tab_personal, self.navigation_icon(), 'Personal')
        self.tab_widget.addTab(self.tab_social, 'Social')
        self.tab_widget.addTab(self.tab_promotions, 'Promotions')
        self.tab_widget.addTab(self.tab_updates, 'Updates')

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/inbox_icon.png'))
        return self.icon

    def execute_viewmodels(self):
        # This might not be desired behaviour, maybe we do want emidiate viewmodel execution
        # as they will spend most of their time in another thread.
        self.vm_personal.run()
        self.vm_social.run()
        self.vm_promotions.run()
        self.vm_updates.run()

    def _bind_list_page_switch(self, paged_list, view_model):
        paged_list.pagedIndexBox.next.clicked.connect(view_model.load_next)
        paged_list.pagedIndexBox.previous.clicked.connect(view_model.load_prev)


class ContactsPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.paged_list = PagedList(size=(200, 200))
        self.vm = ContactsViewModel()
        self.okbtn = QPushButton('OK')
        self.cancelbtn = QPushButton('Cancel')

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
        self.vm = MessagesViewModel('sent')
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
        self.vm = ContactsViewModel()
        #self.paged_list.model = self.vm.threads_listmodel
        self.okbtn = QPushButton('OK')
        self.cancelbtn = QPushButton('Cancel')
        self.cancelbtn.clicked.connect(self.close)

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
        self.vm = MessagesViewModel('trash')
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