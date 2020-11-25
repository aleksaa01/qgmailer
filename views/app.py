from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QFont

from views.sidebar import Sidebar
from views.inbox_page import InboxPageView
from views.managers import PageManagerView
from views.send_email_page import SendEmailPageView
from views.contacts_page import ContactsPageView
from views.trash_page import TrashPageView
from views.options_page import OptionsPageView
from views.email_viewer_page import EmailViewerPageView
from views.stylesheets import themes
from channels.event_channels import EmailEventChannel, ContactEventChannel, SidebarEventChannel, OptionEventChannel
from channels.signal_channels import SignalChannel
from services.api import APIService
from views.icons import icons_rc

from qmodels.options import options


class AppController(object):
    on_themechanged = SignalChannel(str)
    on_fontsizechanged = SignalChannel(int)

    def __init__(self):
        OptionEventChannel.subscribe('theme', self.handle_theme_changed)
        OptionEventChannel.subscribe('font_size', self.handle_font_size_changed)

    def handle_theme_changed(self, message):
        theme = message.get('value')
        self.on_themechanged.emit(theme)

    def handle_font_size_changed(self, message):
        font_size = message.get('value')
        self.on_fontsizechanged.emit(font_size)


class AppView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.c = AppController()
        self.c.on_themechanged.connect(self.set_theme)
        self.c.on_fontsizechanged.connect(self.set_font_size)

        self.api_service = APIService()

        # TODO: Move this event channel configuration to controller if possible.
        EmailEventChannel.subscribe(
            'email_request',
            lambda message: self.handle_request(EmailEventChannel, 'email_response', message)
        )
        EmailEventChannel.subscribe(
            'page_request',
            lambda message: self.handle_request(EmailEventChannel, 'page_response', message)
        )
        EmailEventChannel.subscribe(
            'send_email',
            lambda message: self.handle_request(EmailEventChannel, 'email_sent', message)
        )
        ContactEventChannel.subscribe(
            'page_request',
            lambda message: self.handle_request(ContactEventChannel, 'page_response', message)
        )

        self.setWindowTitle('QGmailer')
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        self.resize(800, 550)

        # cw - central widget
        self.cw = QWidget(self)

        self.sidebar = Sidebar(parent=self.cw)
        self.page_manager = PageManagerView(parent=self.cw)

        self.inbox_page = InboxPageView()
        self.page_manager.add_page(self.inbox_page)

        self.send_email_page = SendEmailPageView()
        self.page_manager.add_page(self.send_email_page)

        self.contacts_page = ContactsPageView()
        self.page_manager.add_page(self.contacts_page)

        self.trash_page = TrashPageView()
        self.page_manager.add_page(self.trash_page)

        self.options_page = OptionsPageView()
        self.page_manager.add_page(self.options_page)

        self.email_viewer_page = EmailViewerPageView()
        self.page_manager.add_page(self.email_viewer_page)

        self.page_manager.add_rule(self.send_email_page, ContactEventChannel, 'contact_picked')
        self.page_manager.add_rule(self.contacts_page, ContactEventChannel, 'pick_contact')
        self.page_manager.add_rule(self.email_viewer_page, EmailEventChannel, 'email_response')

        self.page_manager.add_rule(self.inbox_page, SidebarEventChannel, 'inbox_page')
        self.page_manager.add_rule(self.send_email_page, SidebarEventChannel, 'send_email_page')
        self.page_manager.add_rule(self.contacts_page, SidebarEventChannel, 'contacts_page')
        self.page_manager.add_rule(self.trash_page, SidebarEventChannel, 'trash_page')
        self.page_manager.add_rule(self.options_page, SidebarEventChannel, 'options_page')
        self.page_manager.change_to_index(0)

        mlayout = QHBoxLayout()
        mlayout.addWidget(self.sidebar)
        mlayout.addWidget(self.page_manager)
        self.cw.setLayout(mlayout)
        self.set_theme(options.theme)
        self.set_font_size(options.font_size)
        self.setCentralWidget(self.cw)

    def handle_request(self, event_channel, topic, request_message):
        callback = lambda response_message: self.handle_response(event_channel, topic, response_message)
        category = request_message.get('category')
        value = request_message.get('value')
        self.api_service.fetch(category, value, callback)

    def handle_response(self, event_channel, topic, api_event):
        print(f'In handle_response. event_channel({event_channel}), topic({topic}), category({api_event.category})')
        message = {'category': api_event.category, 'value': api_event.value}
        event_channel.publish(topic, message)

    def set_theme(self, theme):
        print(f'Changing theme({theme})')
        self.cw.setStyleSheet(themes[theme])

    def set_font_size(self, font_size):
        print(f'Changing font size({font_size})')
        font = QFont()
        font.setPixelSize(font_size)
        QApplication.setFont(font)
        self.cw.setStyleSheet(self.cw.styleSheet())

    def closeEvent(self, event):
        self.hide()

        self.api_service.shutdown()
        event.accept()

