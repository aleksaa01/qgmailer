from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog, QStackedWidget, \
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QApplication, \
    QSizePolicy, QLineEdit, QTextEdit, QToolButton, QSpacerItem, QComboBox
from PyQt5.QtGui import QPixmap, QIcon, QPalette
from PyQt5.QtCore import QSize, QRect, Qt
from views.custom_widgets import PagedList, OptionsWidget
from viewmodels_mvvm.messages import MessagesViewModel
from viewmodels_mvvm.contacts import ContactsViewModel
from viewmodels_mvvm.options import OptionsViewModel

import time


class AppView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('QGmailer')
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        self.resize(640, 480)

        # cw - central widget
        self.cw = QWidget(self)
        palettecw = QPalette()
        palettecw.setColor(QPalette.Background, Qt.black)
        self.cw.setAutoFillBackground(True)
        self.cw.setPalette(palettecw)

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
        self.options_page = OptionsPage(self.switcher)
        self.add_page(self.options_page)

        self.sidebar = SidebarNavigation(self.switcher, self.pages, self.cw)

        layout = QHBoxLayout()
        layout.addWidget(self.sidebar)
        layout.addWidget(self.switcher)
        self.cw.setLayout(layout)
        self.setCentralWidget(self.cw)
        palette = QPalette()
        palette.setColor(QPalette.Background, Qt.blue)
        palette2 = QPalette()
        palette2.setColor(QPalette.Background, Qt.red)

        self.switcher.setAutoFillBackground(True)
        self.switcher.setPalette(palette)
        self.sidebar.setAutoFillBackground(True)
        self.sidebar.setPalette(palette2)
        self.show()

        self.load()

    def add_page(self, page):
        self.pages.append(page)
        self.switcher.addWidget(page)

    def load(self):
        QApplication.processEvents()
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
        self.list_personal = PagedList(None, parent=self.tab_personal)
        self.vm_personal = MessagesViewModel('personal')
        self.list_personal.model = self.vm_personal.threads_listmodel
        self._bind_list_page_switch(self.list_personal, self.vm_personal)
        self.vm_personal.on_loading(lambda: self.list_personal.pagedIndexBox.next.setDisabled(True))
        self.vm_personal.on_loaded(lambda: self.list_personal.pagedIndexBox.next.setEnabled(True))
        layout = QVBoxLayout()
        layout.addWidget(self.list_personal)
        self.tab_personal.setLayout(layout)

        self.tab_social = QWidget()
        self.list_social = PagedList(None, (200, 200), self.tab_social)
        self.vm_social = MessagesViewModel('social')
        self.list_social.model = self.vm_social.threads_listmodel
        layout = QVBoxLayout()
        layout.addWidget(self.list_social)
        self.tab_social.setLayout(layout)

        self.tab_promotions = QWidget()
        self.list_promotions = PagedList(None, (200, 200), self.tab_promotions)
        self.vm_promotions = MessagesViewModel('promotions')
        self.list_promotions.model = self.vm_promotions.threads_listmodel
        layout = QVBoxLayout()
        layout.addWidget(self.list_promotions)
        self.tab_promotions.setLayout(layout)

        self.tab_updates = QWidget()
        self.list_updates = PagedList(None, (200, 200), self.tab_updates)
        self.vm_updates = MessagesViewModel('updates')
        self.list_updates.model = self.vm_updates.threads_listmodel
        layout = QVBoxLayout()
        layout.addWidget(self.list_updates)
        self.tab_updates.setLayout(layout)

        self.tab_widget.addTab(self.tab_personal, self.navigation_icon(), 'Personal')
        self.tab_widget.addTab(self.tab_social, 'Social')
        self.tab_widget.addTab(self.tab_promotions, 'Promotions')
        self.tab_widget.addTab(self.tab_updates, 'Updates')

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)

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

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_contacts = QWidget()
        self.list_contacts = PagedList(size=(200, 200))
        self.vm_contacts = ContactsViewModel()
        self.list_contacts.model = self.vm_contacts.contacts_listmodel
        self.list_contacts.pagedIndexBox.next.clicked.connect(self.vm_contacts.load_next)
        self.list_contacts.pagedIndexBox.previous.clicked.connect(self.vm_contacts.load_prev)

        layout = QVBoxLayout()
        layout.addWidget(self.list_contacts)
        self.tab_contacts.setLayout(layout)

        self.tab_widget.addTab(self.tab_contacts, self.navigation_icon(), 'Contacts')

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/contacts_icon2.png'))
        return self.icon

    def execute_viewmodels(self):
        self.vm_contacts.run()


class SentPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_sent = QWidget()
        self.list_sent = PagedList(parent=self.tab_sent)
        self.vm_sent = MessagesViewModel('sent')
        self.list_sent.model = self.vm_sent.threads_listmodel
        self._bind_list_page_switch(self.list_sent, self.vm_sent)
        self.vm_sent.on_loading(lambda: self.list_sent.pagedIndexBox.next.setDisabled(True))
        self.vm_sent.on_loaded(lambda: self.list_sent.pagedIndexBox.next.setEnabled(True))
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(self.list_sent)
        self.tab_sent.setLayout(tab_layout)

        self.tab_widget.addTab(self.tab_sent, self.navigation_icon(), 'Sent')
        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/sent_icon.png'))
        return self.icon

    def execute_viewmodels(self):
        self.vm_sent.run()

    def _bind_list_page_switch(self, paged_list, view_model):
        paged_list.pagedIndexBox.next.clicked.connect(view_model.load_next)
        paged_list.pagedIndexBox.previous.clicked.connect(view_model.load_prev)


class SendEmailPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.to_edit = QLineEdit(self)
        self.to_edit.setMaximumSize(250, 30)
        self.to_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.to_edit.setPlaceholderText('To')
        self.subject_edit = QLineEdit(self)
        self.subject_edit.setPlaceholderText('Subject')
        self.subject_edit.setMaximumHeight(30)
        self.subject_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.message_text = QTextEdit(self)
        self.add_contact_btn = QToolButton(self)
        self.send_email = QPushButton('Send', self)
        self.send_email.setMaximumSize(60, 40)
        self.send_email.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        tolayout = QHBoxLayout()
        tolayout.addWidget(self.to_edit)
        tolayout.addWidget(self.add_contact_btn)
        tolayout.addStretch(0)

        mlayout = QVBoxLayout()
        mlayout.addLayout(tolayout)
        mlayout.addWidget(self.subject_edit)
        mlayout.addWidget(self.message_text)
        mlayout.addWidget(self.send_email)
        self.setLayout(mlayout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/send_icon.png'))
        return self.icon

    def execute_viewmodels(self):
        return


class TrashPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_trash = QWidget()
        self.list_trash = PagedList(parent=self.tab_trash)
        self.vm_trash = MessagesViewModel('trash')
        self.list_trash.model = self.vm_trash.threads_listmodel
        self.vm_trash.on_loading(lambda: self.list_trash.pagedIndexBox.next.setDisabled(True))
        self.vm_trash.on_loaded(lambda: self.list_trash.pagedIndexBox.next.setDisabled(True))
        self._bind_switch_page(self.list_trash, self.vm_trash)
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(self.list_trash)
        self.tab_trash.setLayout(tab_layout)

        self.tab_widget.addTab(self.tab_trash, self.navigation_icon(),'Trash')
        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)

    def _bind_switch_page(self, paged_list, view_model):
        paged_list.pagedIndexBox.next.clicked.connect(view_model.load_next)
        paged_list.pagedIndexBox.previous.clicked.connect(view_model.load_prev)

        # self.vm_sent.on_loading(lambda: self.list_sent.pagedIndexBox.next.setDisabled(True))
        # self.vm_sent.on_loaded(lambda: self.list_sent.pagedIndexBox.next.setEnabled(True))
        # layout = QVBoxLayout()
        # layout.addWidget(self.list_sent)
        # self.tab_sent.setLayout(layout)
        #
        # self.tab_widget.addTab(self.tab_sent, self.navigation_icon(), 'Sent')
        # layout = QVBoxLayout()
        # layout.addWidget(self.tab_widget)
        # self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/trash_icon.png'))
        return self.icon

    def execute_viewmodels(self):
        self.vm_trash.run()


class OptionsPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon = None

        self.vm_options = OptionsViewModel()
        widget = OptionsWidget(self.vm_options.all_options(), self.vm_options.current_options(), self)
        layout = QVBoxLayout()
        layout.addWidget(widget)
        self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/options_button.png'))
        return self.icon

    def execute_viewmodels(self):
        return


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