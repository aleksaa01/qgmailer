from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap

from views.inbox_page import InboxPageView
from views.managers import PageManagerView
from views.send_email_page import SendEmailPageView
from views.contacts_page import ContactsPageView
from channels.event_channels import EmailEventChannel


class AppView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('QGmailer')
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        self.resize(800, 550)

        # cw - central widget
        self.cw = QWidget(self)

        self.page_manager = PageManagerView()

        self.inbox_page = InboxPageView()
        self.page_manager.add_page(self.inbox_page)
        self.email_viewer_page = None
        # self.page_manager.add_page(self.email_viewer_page)

        self.send_email_page = SendEmailPageView()
        self.page_manager.add_page(self.send_email_page)

        self.contacts_page = ContactsPageView()
        self.page_manager.add_page(self.contacts_page)

        self.page_manager.add_rule(self.email_viewer_page, EmailEventChannel, 'email_request')
        self.page_manager.change_to_index(1)

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.page_manager)
        self.cw.setLayout(mlayout)
        self.setCentralWidget(self.cw)
