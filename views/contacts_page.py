from PyQt5.QtWidgets import QTabWidget, QWidget, QPushButton, \
    QSizePolicy, QVBoxLayout

from views.lists import ContactListView
from qmodels.contact import ContactModel


class ContactsPageController(object):

    def __init__(self):
        pass


class ContactsPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.c = ContactsPageController()

        self.conmod = ContactModel('contacts')

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_contacts = QWidget()
        # TODO: Add an action and a method for contact removal
        self.list_contacts = ContactListView('contacts', None, parent=self.tab_contacts)
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
        # dialog = AddContactDialog(self.vm_contacts, self)
        # dialog.exec_()
        return
