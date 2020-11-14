from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap

from views.inbox_page import InboxPageView
from views.managers import PageManagerView
from views.send_email_page import SendEmailPageView
from views.contacts_page import ContactsPageView
from channels.event_channels import EmailEventChannel, ContactEventChannel
from services.api import APIService


class AppView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.api_service = APIService()

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
        self.page_manager.change_to_index(0)

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.page_manager)
        self.cw.setLayout(mlayout)
        self.setCentralWidget(self.cw)
        print('setup done.')

    def handle_request(self, event_channel, topic, request_message):
        callback = lambda response_message: self.handle_response(event_channel, topic, response_message)
        category = request_message.get('category')
        value = request_message.get('value')
        self.api_service.fetch(category, value, callback)

    def handle_response(self, event_channel, topic, api_event):
        print(f'In handle_response. event_channel({event_channel}), topic({topic}), category({api_event.category})')
        message = {'category': api_event.category, 'value': api_event.value}
        event_channel.publish(topic, message)

    def closeEvent(self, event):
        self.hide()

        self.api_service.shutdown()
        event.accept()

