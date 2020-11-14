from PyQt5.QtWidgets import QLineEdit, QTextEdit, QToolButton, QSizePolicy, QHBoxLayout, \
    QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize, QTimer

from channels.event_channels import EmailEventChannel
from channels.signal_channels import SignalChannel

from email.mime.text import MIMEText
from base64 import urlsafe_b64encode


class SendEmailPageController(object):
    on_email_response = SignalChannel(bool)
    
    def __init__(self):
        EmailEventChannel.subscribe('email_sent', self.handle_response)

    def send_email(self, to, subject, message):
        mime_msg = MIMEText(message)
        mime_msg['to'] = to
        mime_msg['subject'] = subject

        email_msg = {'raw': urlsafe_b64encode(mime_msg.as_string())}

        event_msg = {'category': 'send_email', 'value': email_msg}
        EmailEventChannel.publish('send_email', event_msg)

    def handle_response(self, message):
        response = message.value
        if response.error:
            # TODO: Create new signal on_email_error and display some useful message
            # An error occurred, display an error message, and a reason.
            print('Email not sent, error:', response.reason)
            self.on_email_response.emit(False)
        self.on_email_response.emit(True)


class SendEmailPageView(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.c = SendEmailPageController()
        self.c.on_email_response.connect(self.handle_response)
        
        self.to_edit = QLineEdit(self)  # TODO: Make more sophisticated line edit.
        self.to_edit.setMaximumSize(250, 30)
        self.to_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.to_edit.setPlaceholderText('To')
        
        self.subject_edit = QLineEdit(self)
        self.subject_edit.setPlaceholderText('Subject')
        self.subject_edit.setMaximumHeight(30)
        self.subject_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.message_text = QTextEdit(self)
        self.pick_contacts_btn = QToolButton(self)
        self.pick_contacts_btn.setFixedSize(30, 30)
        self.pick_contacts_btn.setObjectName('findContactsBtn')
        self.pick_contacts_btn.clicked.connect(self.pick_contact)
        icon = QIcon(QPixmap(':/images/choose_contact_btn.png'))
        self.pick_contacts_btn.setIcon(icon)
        self.pick_contacts_btn.setIconSize(QSize(32, 32))
        self.pick_contacts_btn.setStyleSheet(
            '#findContactsBtn {background: transparent; border: none;} #findContactsBtn:hover {background: \"#b3b3b3\"; border-radius: 15px;}'
        )
        
        self.send_email_btn = QPushButton('Send', self)
        self.send_email_btn.setMaximumSize(60, 40)
        self.send_email_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.send_email_btn.clicked.connect(self.send_email)
        self.send_email_message = QLabel('', self)
        
        send_layout = QHBoxLayout()
        send_layout.addWidget(self.send_email_btn)
        send_layout.addWidget(self.send_email_message)
        send_layout.addStretch(0)
        
        tolayout = QHBoxLayout()
        tolayout.addWidget(self.to_edit)
        tolayout.addWidget(self.pick_contacts_btn)
        tolayout.addStretch(0)
        
        mlayout = QVBoxLayout()
        mlayout.addLayout(tolayout)
        mlayout.addWidget(self.subject_edit)
        mlayout.addWidget(self.message_text)
        mlayout.addLayout(send_layout)
        self.setLayout(mlayout)

    def pick_contact(self):
        return

    def add_contact(self, email):
        # TODO: Rename this method, it's really bad
        if not email:
            return
        text = self.to_edit.text()
        if text:
            text += ', '
        text += email
        self.to_edit.setText(text)
    
    def send_email(self):
        to = self.to_edit.text()
        subject = self.subject_edit.text()
        text = self.message_text.toPlainText()
        self.c.send_email(to, subject, text)

    def handle_response(self, success):
        if success is True:
            self.send_email_message.setStyleSheet('color: green;')
            self.send_email_message.setText('Email sent successfully !')
        elif success is False:
            self.send_email_message.setStyleSheet('color: red;')
            self.send_email_message.setText('Email wasn\'t sent !')
        self.send_email_message.show()
        
        QTimer.singleShot(5 * 1000, lambda: self.send_email_message.hide())
