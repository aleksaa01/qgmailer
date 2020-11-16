from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QPixmap

from channels.event_channels import SidebarEventChannel


class Sidebar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()

        inbox_btn = QPushButton()
        icon = QIcon(QPixmap(':/images/inbox_icon.png'))
        inbox_btn.setIcon(icon)
        inbox_btn.setIconSize(QSize(40, 40))
        inbox_btn.clicked.connect(lambda: self.emit_event('inbox_page'))

        send_email_btn = QPushButton()
        icon = QIcon(QPixmap(':/images/send_icon.png'))
        send_email_btn.setIcon(icon)
        send_email_btn.setIconSize(QSize(40, 40))
        send_email_btn.clicked.connect(lambda: self.emit_event('send_email_page'))

        contacts_page_btn = QPushButton()
        icon = QIcon(QPixmap(':/images/contacts_icon2.png'))
        contacts_page_btn.setIcon(icon)
        contacts_page_btn.setIconSize(QSize(40, 40))
        contacts_page_btn.clicked.connect(lambda: self.emit_event('contacts_page'))

        trash_page_btn = QPushButton()
        icon = QIcon(QPixmap(':/images/trash_icon.png'))
        trash_page_btn.setIcon(icon)
        trash_page_btn.setIconSize(QSize(40, 40))
        trash_page_btn.clicked.connect(lambda: self.emit_event('trash_page'))

        options_page_btn = QPushButton()
        icon = QIcon(QPixmap(':/images/options_button.png'))
        options_page_btn.setIcon(icon)
        options_page_btn.setIconSize(QSize(40, 40))
        options_page_btn.clicked.connect(lambda: self.emit_event('options_page'))

        self.layout.addWidget(inbox_btn)
        self.layout.addWidget(send_email_btn)
        self.layout.addWidget(contacts_page_btn)
        self.layout.addWidget(trash_page_btn)
        self.layout.addWidget(options_page_btn)
        self.setLayout(self.layout)

    def emit_event(self, topic):
        SidebarEventChannel.publish(topic, {})

