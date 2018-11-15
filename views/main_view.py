from views.gen_view import Ui_MainWindow
from views.custom_widgets import PagedList, EmailViewer, OptionsDialog
from options import Options

from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import QTimer

from os.path import splitext as split_extension


INBOX_PAGE = 0
SEND_PAGE = 1
CONTACTS_PAGE = 2
SENT_MAIL_PAGE = 3
TRASH_PAGE = 4
EMAIL_VIEWER_PAGE = 5


class MainView(QMainWindow):

    EMAIL_TYPES = ('personal', 'social', 'promotions', 'updates', 'sent', 'trash')
    # these containers are just layouts.
    EMAIL_TYPE_CONTAINERS = ('personalDiv', 'socialDiv', 'promotionsDiv', 'updatesDiv', 'sentDiv', 'trashDiv')
    CONTACTS_TYPE_CONTAINERS = ('contactsDiv', )

    def __init__(self, dispatcher, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.stackedWidget.currentChanged.connect(self.handle_page_change)

        self.email_lists = []
        for type, container in zip(self.EMAIL_TYPES, self.EMAIL_TYPE_CONTAINERS):
            email_list = PagedList(type=type)
            getattr(self.ui, container).addWidget(email_list)
            #getattr(self.ui, container).setStyleSheet('background-color: gray;')
            self.email_lists.append(email_list)

        self.contacts_lists = []
        for container in self.CONTACTS_TYPE_CONTAINERS:
            contact_list = PagedList()
            getattr(self.ui, container).addWidget(contact_list)
            self.contacts_lists.append(contact_list)

        self.dispatcher = dispatcher

        self.email_viewer = None

        # In order to show window first, we need to delay setting up
        # the Dispatcher and everything else, so that initializer can finish.
        # after which windows shows up and app runs.
        QTimer.singleShot(100, self.setup_dispatcher)

    def setup_dispatcher(self):
        self.create_email_viewer()
        self.dispatcher.register_email_viewer(self.email_viewer)

        for i in range(len(self.email_lists)):
            self.dispatcher.register_email_list(self.email_lists[i])
        for i in range(len(self.contacts_lists)):
            self.dispatcher.register_contact_list(self.contacts_lists[i], self.ui.toLineEdit)

        self.link_sidebar()

        for elist in self.email_lists:
            elist.link_navigation()
            elist.link_items(self.switch_to_viewer)
            elist.link_indexes()
        for clist in self.contacts_lists:
            clist.link_navigation()
            clist.link_items(self.switch_to_send_page)
            clist.link_indexes()

        self.ui.sendMessageBtn.clicked.connect(self.send_email_fields)

        self.dispatcher.start()

    def switch_page(self, page):
        self.ui.stackedWidget.setCurrentIndex(page)

    def switch_to_viewer(self):
        self.ui.stackedWidget.setCurrentIndex(EMAIL_VIEWER_PAGE)

    def switch_to_send_page(self):
        self.ui.stackedWidget.setCurrentIndex(SEND_PAGE)

    def create_email_viewer(self):
        self.email_viewer = EmailViewer()
        self.email_viewer.fileExtracted.connect(self.run_save_dialog)
        self.ui.layoutQWebEngine.addWidget(self.email_viewer)

    def link_sidebar(self):
        self.ui.sideBarInbox.clicked.connect(lambda: self.switch_page(INBOX_PAGE))
        self.ui.sideBarSend.clicked.connect(lambda: self.switch_page(SEND_PAGE))
        self.ui.sideBarContacts.clicked.connect(lambda: self.switch_page(CONTACTS_PAGE))
        self.ui.sideBarSent.clicked.connect(lambda: self.switch_page(SENT_MAIL_PAGE))
        self.ui.sideBarTrash.clicked.connect(lambda: self.switch_page(TRASH_PAGE))
        self.ui.sideBarSettings.clicked.connect(self.run_options_dialog)

    def handle_page_change(self, new_index):
        print('Page CHANGED !')
        if new_index != EMAIL_VIEWER_PAGE:
            self.email_viewer.stop_extracting = True
        else:
            self.email_viewer.stop_extracting = False

    def send_email_fields(self):
        self.dispatcher.send_email(
            self.ui.toLineEdit.text(),
            self.ui.subjectLineEdit.text(),
            self.ui.messageTextEdit.toPlainText()
        )

    def run_save_dialog(self, filename, file):
        print('Save dialog opened...')
        name, extension = split_extension(filename)
        filepath, _ = QFileDialog.getSaveFileName(self, 'Save file', '/' + filename)
        if filepath:
            self.dispatcher.save_file(filepath + extension, file)

    def run_options_dialog(self):
        dialog = OptionsDialog(Options)
        dialog.exec_()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = MainView()
    window.show()
    app.exec_()