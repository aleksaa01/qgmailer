from PyQt5.QtWidgets import QTabWidget, QWidget, QPushButton, \
    QSizePolicy, QVBoxLayout

from views.lists.lists import ContactListView
from views.dialogs import AddContactDialog
from qmodels.contact import ContactModel


class ContactsPageController(object):

    def __init__(self, model):
        self.model = model

    def add_contact(self, name, email):
        self.model.add_contact(name, email)


# TODO: Add "Other Contacts" list.
# TODO: Add cover photos to the list(and ability to change them, or add them).
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
        # Setting minimum size will allow widget to grow when font size is increased.
        # Setting size policy to maximum won't allow the widget to be stretch by layout,
        # which happens vertically for QHBoxLayout and horizontally for QVBoxLayout.
        self.add_contact_btn.setMinimumSize(80, 40)
        self.add_contact_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.tab_widget.addTab(self.tab_contacts, 'Contacts')

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        mlayout.addWidget(self.add_contact_btn)
        self.setLayout(mlayout)

    def run_add_contact_dialog(self):
        dialog = AddContactDialog()
        dialog.contact_created.connect(self.c.add_contact)
        dialog.exec_()

