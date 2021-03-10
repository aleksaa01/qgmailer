from PyQt5.QtWidgets import QLineEdit, QTextEdit, QToolButton, QSizePolicy, QHBoxLayout, \
    QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import QSize, QTimer

from googleapis.gmail.labels import LABEL_ID_SENT
from channels.event_channels import EmailEventChannel, ContactEventChannel, \
    OptionEventChannel
from channels.signal_channels import SignalChannel
from qmodels.options import options
from views.buttons import AnimatedButton

from email.mime.text import MIMEText
from base64 import urlsafe_b64encode


class SendEmailPageController(object):
    on_email_sent = SignalChannel(bool)
    on_contact_picked = SignalChannel(str)
    
    def __init__(self):
        EmailEventChannel.subscribe('email_sent', self.handle_email_sent)
        ContactEventChannel.subscribe('contact_picked', self.handle_contact_picked)

    def send_email(self, to, subject, message):
        mime_msg = MIMEText(message)
        mime_msg['to'] = to
        mime_msg['subject'] = subject

        email_msg = {'raw': urlsafe_b64encode(mime_msg.as_bytes()).decode('utf-8')}

        EmailEventChannel.publish('send_email', label_id=LABEL_ID_SENT, email_msg=email_msg)

    def handle_email_sent(self, label_id, email, error=''):
        if error:
            self.on_email_sent.emit(False)
        self.on_email_sent.emit(True)

    def handle_contact_picked(self, email):
        self.on_contact_picked.emit(email)

    def pick_contact(self):
        ContactEventChannel.publish('pick_contact')


class SendEmailPageView(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)

        pressed_hover = '#PickContacts:pressed:hover{border-radius: 16%%;}'
        self.dark_style = pressed_hover + '#PickContacts{border: 0px; border-radius: 17%%; background-color: rgba(255, 255, 255, %s);}'
        self.default_style = pressed_hover + '#PickContacts{border: 0px; border-radius: 17%%; background-color: rgba(0, 0, 0, %s);}'
        if options.theme == 'dark':
            color = QColor(255, 255, 255, 200)
            self.current_style = self.dark_style
        else:
            self.current_style = self.default_style
            color = QColor(0, 0, 0, 255)

        self.c = SendEmailPageController()
        self.c.on_email_sent.connect(self.handle_response)
        self.c.on_contact_picked.connect(self.add_recipient)
        
        self.to_edit = QLineEdit(self)  # TODO: Make more sophisticated line edit.
        self.to_edit.setMaximumSize(250, 30)
        self.to_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.to_edit.setPlaceholderText('To')
        
        self.subject_edit = QLineEdit(self)
        self.subject_edit.setPlaceholderText('Subject')
        self.subject_edit.setMaximumHeight(30)
        self.subject_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.message_text = QTextEdit(self)
        self.pick_contacts_btn = AnimatedButton(
            lambda button, new_val: button.setStyleSheet(self.current_style % new_val),
            anim_end=50, anim_duration=200
        )
        self.pick_contacts_btn.setObjectName('PickContacts')
        icon = self._prepare_pixmap(QPixmap(':/images/choose_contact_btn.png'), color)
        self.pick_contacts_btn.setIcon(icon)
        self.pick_contacts_btn.setIconSize(QSize(28, 28))
        self.pick_contacts_btn.setFixedSize(QSize(35, 35))
        self.pick_contacts_btn.setStyleSheet(self.current_style)
        self.pick_contacts_btn.clicked.connect(self.pick_contact)
        
        self.send_email_btn = QPushButton('Send', self)
        # Setting minimum size will allow widget to grow when font size is increased.
        # Setting size policy to maximum won't allow the widget to be stretch by layout,
        # which happens vertically for QHBoxLayout and horizontally for QVBoxLayout.
        self.send_email_btn.setMinimumSize(60, 40)
        self.send_email_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
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

        OptionEventChannel.subscribe('theme', self.update_icons)

    def pick_contact(self):
        self.c.pick_contact()

    def add_recipient(self, email):
        if not email:
            return
        text = self.to_edit.text()
        if text:
            emails = text.split(', ')
            if email in emails:
                return
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

    def update_icons(self, theme):
        if theme == 'dark':
            color = QColor(255, 255, 255, 200)
            self.current_style = self.dark_style
        else:
            self.current_style = self.default_style
            color = QColor(0, 0, 0, 255)

        pix = self.pick_contacts_btn.icon().pixmap(QSize(28, 28))
        self.pick_contacts_btn.setIcon(self._prepare_pixmap(pix, color))

    def _prepare_pixmap(self, pixmap, qcolor):
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        painter.fillRect(pixmap.rect(), qcolor)
        painter.end()
        return QIcon(pixmap)
