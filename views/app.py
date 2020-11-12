from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtGui import QIcon, QPixmap

from views.inbox_page import InboxPageView
from views.managers import PageManagerView
from channels.event_channels import EmailEventChannel


class AppView(QMainWindow):

    def __init__(self):
        self.setWindowTitle('QGmailer')
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        self.resize(640, 480)

        # cw - central widget
        self.cw = QWidget(self)

        self.page_manager = PageManagerView()

        self.inbox_page = InboxPageView()
        self.page_manager.add_page(self.inbox_page)
        self.email_viewer_page = None
        #self.page_manager.add_page(self.email_viewer_page)

        self.page_manager.add_rule(self.email_viewer_page, EmailEventChannel, 'email_request')
