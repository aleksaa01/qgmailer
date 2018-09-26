from views.gen_view import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer


INBOX_PAGE = 0
SEND_PAGE = 1
CONTACTS_PAGE = 2
SENT_MAIL_PAGE = 3
TRASH_PAGE = 4
WEBENGINE_PAGE = 5


class MainView(QMainWindow):

    def __init__(self, dispatcher, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.dispatcher = dispatcher

        # In order to show window first, we need NOT to create,
        # register, and then run everything in initializer.
        QTimer.singleShot(100, self.setup_dispatcher)

    def setup_dispatcher(self):
        self.link_sidebar()
        self.create_web_stuff()
        self.dispatcher.register_webview(self.web_page)

        self.dispatcher.register_widget(self.ui.personalListView, 'personal')
        self.dispatcher.register_widget(self.ui.socialListView, 'social')
        self.dispatcher.register_widget(self.ui.promotionsListView, 'promotions')
        self.dispatcher.register_widget(self.ui.updatesListView, 'updates')

        self.ui.personalListView.clicked.connect(lambda: self.switch_page(WEBENGINE_PAGE))

        self.dispatcher.start()

    def switch_page(self, page):
        self.ui.stackedWidget.setCurrentIndex(page)

    def create_web_stuff(self):
        self.web_engine = QWebEngineView()
        # ERASE THIS SHIT AND SET LAYOUT IN QtDesigner,
        # so you can just add widget in here.
        layout = QHBoxLayout()
        layout.addWidget(self.web_engine)
        self.ui.containerQWebEngine.setLayout(layout)
        self.web_page = self.web_engine.page()

    def link_sidebar(self):
        self.ui.sideBarInbox.clicked.connect(lambda: self.switch_page(INBOX_PAGE))
        self.ui.sideBarSend.clicked.connect(lambda: self.switch_page(SEND_PAGE))
        self.ui.sideBarContacts.clicked.connect(lambda: self.switch_page(CONTACTS_PAGE))