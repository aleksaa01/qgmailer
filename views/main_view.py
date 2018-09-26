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


# TODO: Create new Widget that contains list view, next/prev buttons and index label.


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
        self.create_web_stuff()
        self.dispatcher.register_webview(self.web_page)

        self.dispatcher.register_widget(self.ui.personalListView, 'personal')
        self.dispatcher.register_widget(self.ui.socialListView, 'social')
        self.dispatcher.register_widget(self.ui.promotionsListView, 'promotions')
        self.dispatcher.register_widget(self.ui.updatesListView, 'updates')

        self.dispatcher.start()

        self.link_sidebar()
        self.link_listview_items()
        self.link_listview_navigation()

    def switch_page(self, page):
        self.ui.stackedWidget.setCurrentIndex(page)

    def create_web_stuff(self):
        self.web_engine = QWebEngineView()
        # remove the layout from here and add it in QtDesigner,
        # so you can just add widget in here.
        layout = QHBoxLayout()
        layout.addWidget(self.web_engine)
        self.ui.containerQWebEngine.setLayout(layout)
        self.web_page = self.web_engine.page()

    def link_sidebar(self):
        self.ui.sideBarInbox.clicked.connect(lambda: self.switch_page(INBOX_PAGE))
        self.ui.sideBarSend.clicked.connect(lambda: self.switch_page(SEND_PAGE))
        self.ui.sideBarContacts.clicked.connect(lambda: self.switch_page(CONTACTS_PAGE))

    def link_listview_items(self):
        self.ui.personalListView.clicked.connect(lambda: self.switch_page(WEBENGINE_PAGE))
        self.ui.socialListView.clicked.connect(lambda: self.switch_page(WEBENGINE_PAGE))
        self.ui.promotionsListView.clicked.connect(lambda: self.switch_page(WEBENGINE_PAGE))
        self.ui.updatesListView.clicked.connect(lambda: self.switch_page(WEBENGINE_PAGE))

    def link_listview_navigation(self):
        self.dispatcher.register_widget_pagination(
            self.ui.personalNextBtn, self.ui.personalPreviousBtn, 'personal')
        self.dispatcher.register_widget_pagination(
            self.ui.socialNextBtn, self.ui.socialPreviousBtn, 'social')
        self.dispatcher.register_widget_pagination(
            self.ui.promotionsNextBtn, self.ui.promotionsPreviousBtn, 'promotions')
        self.dispatcher.register_widget_pagination(
            self.ui.updatesNextBtn, self.ui.updatesPreviousBtn, 'updates')
