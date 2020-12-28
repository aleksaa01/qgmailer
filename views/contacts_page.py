from PyQt5.QtWidgets import QTabWidget, QWidget, QPushButton, \
    QSizePolicy, QVBoxLayout, QDialog, QHBoxLayout, QLabel, \
    QLineEdit
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal

from views.lists import ContactListView
from qmodels.contact import ContactModel

import re


class ContactsPageController(object):

    def __init__(self, model):
        self.model = model

    def add_contact(self, name, email):
        self.model.add_contact(name, email)


class ContactsPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.conmod = ContactModel()
        self.c = ContactsPageController(self.conmod)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_contacts = QWidget()
        self.list_contacts = ContactListView(parent=self.tab_contacts)
        self.list_contacts.set_model(self.conmod)
        layout = QVBoxLayout()
        layout.addWidget(self.list_contacts)
        self.tab_contacts.setLayout(layout)

        self.add_contact_btn = QPushButton('Add Contact')
        self.add_contact_btn.clicked.connect(self.run_add_contact_dialog)
        self.add_contact_btn.setMaximumSize(80, 40)
        self.add_contact_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.tab_widget.addTab(self.tab_contacts, 'Contacts')

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        mlayout.addWidget(self.add_contact_btn)
        self.setLayout(mlayout)

    def run_add_contact_dialog(self):
        dialog = AddContactDialog()
        dialog.contact_created.connect(self.c.add_contact)
        dialog.exec_()


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

