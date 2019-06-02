from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog, QStackedWidget, \
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QApplication, \
    QSizePolicy, QLineEdit, QTextEdit, QToolButton, QSpacerItem, QComboBox
from PyQt5.QtGui import QPixmap, QIcon, QPalette
from PyQt5.QtCore import QSize, QRect, Qt, pyqtSignal
from views.custom_widgets import PagedList, OptionsWidget, EmailViewer, AddContactDialog
from viewmodels.messages import MessagesViewModel
from viewmodels.contacts import ContactsViewModel
from viewmodels.options import OptionsViewModel
from viewmodels.emails import EmailsViewModel
from viewmodels.send_email import SendEmailViewModel

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
        self.options = OptionsViewModel()
        self.cw.setStyleSheet(self.options.extract_theme())
        palettecw = QPalette()
        palettecw.setColor(QPalette.Background, Qt.black)
        self.cw.setAutoFillBackground(True)
        self.cw.setPalette(palettecw)

        self.switcher = QStackedWidget(self.cw)

        self.page_manager = PageManager(self.switcher, self.cw)

        self.email_viewer_page = EmailViewerPage(self.switcher)
        self.page_manager.add_page(self.email_viewer_page)

        self.inbox_page = InboxPage(self.switcher)
        self.page_manager.add_page(self.inbox_page)
        self.sendemail_page = SendEmailPage(self.switcher)
        self.page_manager.add_page(self.sendemail_page)
        self.sent_page = SentPage(self.switcher)
        self.page_manager.add_page(self.sent_page)
        self.contacts_page = ContactsPage(self.switcher)
        self.page_manager.add_page(self.contacts_page)
        self.trash_page = TrashPage(self.switcher)
        self.page_manager.add_page(self.trash_page)
        self.options_page = OptionsPage(self.switcher)
        self.page_manager.add_page(self.options_page)

        self.page_manager.connect('inbox_page', 'item_clicked', self.email_viewer_page.show_email)
        self.page_manager.connect('sent_page', 'item_clicked', self.email_viewer_page.show_email)
        self.page_manager.connect('trash_page', 'item_clicked', self.email_viewer_page.show_email)
        self.page_manager.connect('contacts_page', 'item_clicked', self.sendemail_page.add_contact)
        self.page_manager.connect('sendemail_page', 'find_contacts', self.contacts_page.show_me)
        self.page_manager.switch_to(self.inbox_page.pageid)

        layout = QHBoxLayout()
        layout.addWidget(self.page_manager)
        layout.addWidget(self.switcher)
        self.cw.setLayout(layout)
        self.setCentralWidget(self.cw)
        self.show()

        self.vm_options = OptionsViewModel()
        self.vm_options.register(lambda: self.change_theme())

        self.load()

    def add_page(self, page):
        self.pages.append(page)
        self.switcher.addWidget(page)

    def change_theme(self):
        self.setStyleSheet(self.vm_options.extract_theme())

    def load(self):
        QApplication.processEvents()
        for page in self.page_manager.pages():
            page.execute_viewmodels()


class Page(QWidget):
    """Base class for all Pages."""
    pageid = None
    change_page = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon = None

    def navigation_icon(self):
        raise NotImplementedError('Classes that inherit from Page have to implement navigation_icon method.')

    def execute_viewmodels(self):
        raise NotImplementedError('Classes that inherit from Page have to implement execute_viewmodels method.')

    def receive(self):
        """ This method is used for tranfer of data from some page to this page"""
        raise NotImplementedError('Classes that inherit from Page have to implement receive method')


class InboxPage(Page):
    pageid = 'inbox_page'
    item_clicked = pyqtSignal(str)

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
        self.list_personal.itemclicked.connect(lambda idx: self.handle_itemclicked(idx, self.vm_personal))
        layout = QVBoxLayout()
        layout.addWidget(self.list_personal)
        self.tab_personal.setLayout(layout)

        self.tab_social = QWidget()
        self.list_social = PagedList(None, parent=self.tab_social)
        self.vm_social = MessagesViewModel('social')
        self.list_social.model = self.vm_social.threads_listmodel
        self._bind_list_page_switch(self.list_social, self.vm_social)
        self.vm_social.on_loading(lambda: self.list_social.pagedIndexBox.next.setDisabled(True))
        self.vm_social.on_loaded(lambda: self.list_social.pagedIndexBox.next.setEnabled(True))
        self.list_social.itemclicked.connect(lambda idx: self.handle_itemclicked(idx, self.vm_social))
        layout = QVBoxLayout()
        layout.addWidget(self.list_social)
        self.tab_social.setLayout(layout)

        self.tab_promotions = QWidget()
        self.list_promotions = PagedList(None, (200, 200), self.tab_promotions)
        self.vm_promotions = MessagesViewModel('promotions')
        self.list_promotions.model = self.vm_promotions.threads_listmodel
        self._bind_list_page_switch(self.list_promotions, self.vm_promotions)
        self.vm_promotions.on_loading(lambda: self.list_promotions.pagedIndexBox.next.setDisabled(True))
        self.vm_promotions.on_loaded(lambda: self.list_promotions.pagedIndexBox.next.setEnabled(True))
        self.list_promotions.itemclicked.connect(lambda idx: self.handle_itemclicked(idx, self.vm_promotions))
        layout = QVBoxLayout()
        layout.addWidget(self.list_promotions)
        self.tab_promotions.setLayout(layout)

        self.tab_updates = QWidget()
        self.list_updates = PagedList(None, (200, 200), self.tab_updates)
        self.vm_updates = MessagesViewModel('updates')
        self.list_updates.model = self.vm_updates.threads_listmodel
        self._bind_list_page_switch(self.list_updates, self.vm_updates)
        self.vm_updates.on_loading(lambda: self.list_updates.pagedIndexBox.next.setDisabled(True))
        self.vm_updates.on_loaded(lambda: self.list_updates.pagedIndexBox.next.setEnabled(True))
        self.list_updates.itemclicked.connect(lambda idx: self.handle_itemclicked(idx, self.vm_updates))
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

    def handle_itemclicked(self, index, viewmodel):
        item_id = viewmodel.extract_id(index)
        self.item_clicked.emit(item_id)


class ContactsPage(Page):
    pageid = 'contacts_page'
    item_clicked = pyqtSignal(str)

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
        self.list_contacts.itemclicked.connect(lambda idx: self.handle_item_clicked(idx, self.vm_contacts))

        self.add_contact_btn = QPushButton('Add Contact')
        self.add_contact_btn.clicked.connect(self.run_add_contact_dialog)
        self.add_contact_btn.setMaximumSize(80, 40)
        self.add_contact_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(self.list_contacts)
        self.tab_contacts.setLayout(layout)

        self.tab_widget.addTab(self.tab_contacts, self.navigation_icon(), 'Contacts')

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        mlayout.addWidget(self.add_contact_btn)
        self.setLayout(mlayout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/contacts_icon2.png'))
        return self.icon

    def execute_viewmodels(self):
        self.vm_contacts.run()

    def handle_item_clicked(self, idx, viewmodel):
        email = viewmodel.get_email(idx)
        self.item_clicked.emit(email)

    def run_add_contact_dialog(self):
        dialog = AddContactDialog(self.vm_contacts, self)
        dialog.exec_()

    def show_me(self):
        self.change_page.emit(self.pageid)


class SentPage(Page):
    pageid = 'sent_page'
    item_clicked = pyqtSignal(str)

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
        self.list_sent.itemclicked.connect(lambda idx: self.handle_itemclicked(idx, self.vm_sent))
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

    def handle_itemclicked(self, index, view_model):
        item_id = view_model.extract_id(index)
        self.item_clicked.emit(item_id)


class SendEmailPage(Page):
    pageid = 'sendemail_page'
    find_contacts = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vm_sendemail = SendEmailViewModel()

        self.to_edit = QLineEdit(self) # TODO: Make more sophisticated line edit.
        self.to_edit.setMaximumSize(250, 30)
        self.to_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.to_edit.setPlaceholderText('To')
        self.subject_edit = QLineEdit(self)
        self.subject_edit.setPlaceholderText('Subject')
        self.subject_edit.setMaximumHeight(30)
        self.subject_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.message_text = QTextEdit(self)
        self.find_contacts_btn = QToolButton(self)
        self.find_contacts_btn.setFixedSize(30, 30)
        self.find_contacts_btn.setObjectName('findContactsBtn')
        self.find_contacts_btn.clicked.connect(self.emit_find_contacts)
        icon = QIcon(QPixmap(':/images/choose_contact_btn.png'))
        self.find_contacts_btn.setIcon(icon)
        self.find_contacts_btn.setIconSize(QSize(32, 32))
        self.find_contacts_btn.setStyleSheet('#findContactsBtn {background: transparent; border: none;} #findContactsBtn:hover {background: \"#b3b3b3\"; border-radius: 15px;}')
        self.send_email_btn = QPushButton('Send', self)
        self.send_email_btn.setMaximumSize(60, 40)
        self.send_email_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.send_email_btn.clicked.connect(self.send_email)


        tolayout = QHBoxLayout()
        tolayout.addWidget(self.to_edit)
        tolayout.addWidget(self.find_contacts_btn)
        tolayout.addStretch(0)

        mlayout = QVBoxLayout()
        mlayout.addLayout(tolayout)
        mlayout.addWidget(self.subject_edit)
        mlayout.addWidget(self.message_text)
        mlayout.addWidget(self.send_email_btn)
        self.setLayout(mlayout)

    def emit_find_contacts(self):
        self.find_contacts.emit()

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/send_icon.png'))
        return self.icon

    def execute_viewmodels(self):
        self.vm_sendemail.run()

    def add_contact(self, email):
        if not email:
            return
        text = self.to_edit.text()
        if text:
            text += ', '
        text += email
        self.to_edit.setText(text)
        self.change_page.emit(self.pageid)

    def send_email(self):
        to = self.to_edit.text()
        subject = self.subject_edit.text()
        text = self.message_text.toPlainText()
        self.vm_sendemail.send_email(to, subject, text)


class TrashPage(Page):
    pageid = 'trash_page'
    item_clicked = pyqtSignal(str)

    def __init__(self, email_viewer_page, parent=None):
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
        self.list_trash.itemclicked.connect(lambda idx: self.handle_itemclicked(idx, self.vm_trash))
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

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/trash_icon.png'))
        return self.icon

    def execute_viewmodels(self):
        self.vm_trash.run()

    def handle_itemclicked(self, index, view_model):
        item_id = view_model.extract_id(index)
        self.item_clicked.emit(item_id)


class OptionsPage(Page):
    pageid = 'options_page'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon = None

        self.vm_options = OptionsViewModel()
        self.options_widget = OptionsWidget(self.vm_options.all_options(), self.vm_options.current_options(), self)
        self.apply_btn = QPushButton('Apply', self)
        self.apply_btn.clicked.connect(self._save_options)
        layout = QVBoxLayout()
        layout.addWidget(self.options_widget)
        layout.addWidget(self.apply_btn)
        self.setLayout(layout)

    def navigation_icon(self):
        if self.icon is None:
            self.icon = QIcon(QPixmap(':/images/options_button.png'))
        return self.icon

    def execute_viewmodels(self):
        return

    def _save_options(self):
        options = self.options_widget.get_options()
        self.vm_options.replace_options(options)


class EmailViewerPage(Page):
    pageid = 'emailviewer_page'

    def __init__(self, parent=None):
        super().__init__(parent)

        self.email_viewer = EmailViewer(self)
        self.vm_emailview = EmailsViewModel()
        self.vm_emailview.on_fetched(self.update_content)

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.email_viewer)
        self.setLayout(mlayout)

    def show_email(self, message_id):
        self.vm_emailview.fetch_data(message_id)
        self.change_page.emit(self.pageid)

    def update_content(self, data):
        self.email_viewer.update_content(data)

    def navigation_icon(self):
        return

    def execute_viewmodels(self):
        return



class PageManager(QWidget):
    """
    :param switcher: Some sort of object or widget that can switch between the pages.
    Like QStackedWidget for example, or it can be some custom widget with predefined interface.
    """
    def __init__(self, switcher, parent=None):
        super().__init__(parent)

        self.switcher = switcher
        self.page_map = {}
        self.index_map = {}
        self.page_count = 0

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def add_page(self, page):
        self.switcher.addWidget(page)

        self.index_map[page.pageid] = self.page_count
        self.page_map[page.pageid] = page
        page.change_page.connect(self.switch_to)
        self.page_count += 1

        icon = page.navigation_icon()
        if not icon:
            return

        btn = QPushButton()
        btn.setIcon(icon)
        btn.setIconSize(QSize(40, 40))
        btn.clicked.connect(lambda: self.switch_to(page.pageid))
        self.layout.addWidget(btn)

    def switch_to(self, page_id):
        index = self.index_map[page_id]
        self.switcher.setCurrentIndex(index)

    def connect(self, pageid, signal_name, callback):
        page = self.page_map[pageid]
        getattr(page, signal_name).connect(callback)

    def pages(self):
        return self.page_map.values()


from views.icons import icons_rc