from PyQt5.QtCore import Qt

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import ContactEventChannel, OptionEventChannel


class ContactModel(BaseListModel):

    def __init__(self, category, data=None):
        super().__init__(data)

        self.page_length = options.contacts_per_page
        self.category = category
        self.fetching = False

        ContactEventChannel.subscribe('page_response', self.add_new_page)
        ContactEventChannel.subscribe('contact-removed', self.handle_contact_removed)
        OptionEventChannel.subscribe('contacts_per_page', self.change_page_length)

        # Get first page
        self.fetching = True
        ContactEventChannel.publish('page_request', {'category': self.category})

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._displayed_data[index.row()].get('name')

        elif role == Qt.DecorationRole:
            pass

        elif role == Qt.ToolTipRole:
            pass

    def current_index(self):
        if self.fetching:
            return None, None
        return self.begin, self.end

    def add_new_page(self, message):
        if message.get('category') != self.category:
            return
        self.fetching = False
        if self.end == 0:
            # Model is empty, just add data, don't load next page.
            self.add_data(message.get('value'))
        else:
            data = message.get('value')
            self.add_data(message.get('value'), notify=False)
            self.load_next()

    def emit_email(self, idx):
        ContactEventChannel.publish('contact_picked',
                                  {'category': self.category, 'value': self._displayed_data[idx].get('email')})

    def change_page_length(self, message):
        self.set_page_length(message.get('value'))

    def load_next_page(self):
        if self.end == len(self._data):
            self.fetching = True
            ContactEventChannel.publish('page_request', {'category': self.category})
            return

        self.load_next()

    def load_previous_page(self):
        self.load_previous()

    def remove_contact(self, idx):
        ContactEventChannel.publish('remove_contact', {'category': 'remove_contact', 'value': self._displayed_data[idx].get('resourceName')})
        self._data.pop(self.begin + idx)
        self.end = min(self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_contact_removed(self, message):
        if message.get('category') != 'remove_contact':
            return
        if message.get('value').get('error'):
            # show an error, and try to recover.
            # This would be way easier if data was persisted in a database.
            # But this functionality can be implemented without one, if you separate
            # real data from data to be displayed, and treat them as separate pools.
            # When user removes a contact, then remove data from displayed data, and add
            # from real data, but only remove from real data when you receive response back.
            return
        else:
            print("Contact successfully removed.")
