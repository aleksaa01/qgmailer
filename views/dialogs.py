from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QLineEdit
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

import re


class AddContactDialog(QDialog):

    contact_created = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent=None)
        self.setWindowTitle('Add Contact')
        icon = QIcon()
        icon.addPixmap(QPixmap(":/images/qgmailer_logo.png"), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.name_field = None
        self.email_field = None
        self.EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')

        self.layout = QVBoxLayout()
        self.setup()

        buttons_layout = QHBoxLayout()

        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)
        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.accept)

        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.ok_btn)
        self.layout.addLayout(buttons_layout)
        self.setLayout(self.layout)

    def setup(self):
        fields_layout = QHBoxLayout()
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()

        name_label = QLabel('Name:')
        self.name_field = QLineEdit()
        layout1.addWidget(name_label)
        layout1.addWidget(self.name_field)

        email_label = QLabel('Email:')
        self.email_field = QLineEdit()
        self.email_field.textEdited.connect(lambda e: self.email_field.setStyleSheet(''))
        layout2.addWidget(email_label)
        layout2.addWidget(self.email_field)

        fields_layout.addLayout(layout1)
        fields_layout.addLayout(layout2)
        self.layout.addLayout(fields_layout)

    def accept(self):
        name = self.name_field.text()
        email = self.email_field.text()
        if not self.EMAIL_REGEX.match(email):
            self.email_field.setStyleSheet('border: 1px solid red;')
            return

        self.contact_created.emit(name, email)

        super().accept()


class EditContactDialog(QDialog):

    contact_edited = pyqtSignal(str, str)

    def __init__(self, name, email, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add Contact')
        icon = QIcon()
        icon.addPixmap(QPixmap(":/images/qgmailer_logo.png"), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.contact_name = name
        self.contact_email = email
        self.name_field = None
        self.email_field = None
        self.EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')
        self.layout = QVBoxLayout()
        self.setup()

        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)
        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.accept)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.ok_btn)
        self.layout.addLayout(buttons_layout)
        self.setLayout(self.layout)

    def setup(self):
        fields_layout = QHBoxLayout()
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()

        name_label = QLabel('Name:')
        self.name_field = QLineEdit(self.contact_name)
        layout1.addWidget(name_label)
        layout1.addWidget(self.name_field)

        email_label = QLabel('Email:')
        self.email_field = QLineEdit(self.contact_email)
        self.email_field.textEdited.connect(lambda e: self.email_field.setStyleSheet(''))
        layout2.addWidget(email_label)
        layout2.addWidget(self.email_field)

        fields_layout.addLayout(layout1)
        fields_layout.addLayout(layout2)
        self.layout.addLayout(fields_layout)

    def accept(self):
        name = self.name_field.text()
        email = self.email_field.text()
        if not self.EMAIL_REGEX.match(email):
            self.email_field.setStyleSheet('border: 1px solid red;')
            return

        self.contact_edited.emit(name, email)

        super().accept()


class ErrorReportDialog(QDialog):

    def __init__(self, message, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Error")
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        self.resize(300, 200)

        self.lbl = QLabel(message)
        lay = QVBoxLayout()
        lay.addWidget(self.lbl)
        self.setLayout(lay)
