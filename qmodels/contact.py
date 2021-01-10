from PyQt5.QtCore import Qt

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import ContactEventChannel, OptionEventChannel
from services.sync import SyncHelper


# TODO: Another issue that might come up: How about removing a contact
#   in the middle of "page fetching process". Check if you have to adjust
#   begin and end attributes. Page processing will be blocked during this
#   so you don't have to worry about those kind of inconsistencies.

class ContactModel(BaseListModel):

    def __init__(self, data=None):
        super().__init__(data)

        self.page_length = options.contacts_per_page
        self.fetching = False

        ContactEventChannel.subscribe('page_response', self.add_new_page)
        ContactEventChannel.subscribe('contact_removed', self.handle_contact_removed)
        ContactEventChannel.subscribe('contact_added', self.handle_contact_added)
        OptionEventChannel.subscribe('contacts_per_page', self.change_page_length)

        # Get first page
        self.fetching = True
        ContactEventChannel.publish('page_request')

        self.sync_helper = SyncHelper()

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

    def add_new_page(self, contacts, error=''):
        if error:
            # TODO: Handle this error somehow.
            print("Page request failed... Error: ", error)
            raise Exception()
        self.fetching = False

        if self.end == 0:
            # Model is empty, just add data, don't load next page.
            self.add_data(contacts)
        else:
            self.add_data(contacts, notify=False)
            self.load_next()

    def add_data(self, data, notify=True):
        # Apply unique local IDs
        for row in data:
            row['ulid'] = self.sync_helper.new_ulid()
        super().add_data(data, notify)

    def emit_email(self, idx):
        ContactEventChannel.publish('contact_picked', email=self._displayed_data[idx].get('email'))

    def change_page_length(self, page_length):
        self.set_page_length(page_length)

    def load_next_page(self):
        if self.end == len(self._data):
            self.fetching = True
            ContactEventChannel.publish('page_request')
            return

        self.load_next()

    def load_previous_page(self):
        self.load_previous()

    def remove_contact(self, idx):
        print(f">>> Removing contact at index {idx}:", self._displayed_data[idx].get('email'))
        contact = self._displayed_data[idx]
        topic = 'remove_contact'
        payload = {'resourceName': contact.get('resourceName')}
        # if event list is empty you can send the request, otherwise you have to wait
        # for the response to be processed until you can send another one.
        self.sync_helper.push_event(ContactEventChannel, topic, payload, contact)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_contact_removed(self, error=''):
        if error:
            # TODO: Handle this error. Maybe, drop all data and then resync everything again.
            # Maybe, drop all data and then sync again.
            print("Failed to remove contact...")
            raise Exception()

        # we got a successful response back, now remove the event
        self.sync_helper.pull_event()
        print("Contact completely removed.")
        # Now send next event if there's any left in the queue
        self.sync_helper.push_next_event()

    def add_contact(self, name, email):
        print(f"Adding new contact(name, email): {name}, {email}")
        topic = 'add_contact'
        payload = {'name': name, 'email': email}
        contact = {'name': name, 'email': email, 'ulid': self.sync_helper.new_ulid()}

        self.sync_helper.push_event(ContactEventChannel, topic, payload, contact)

        self._data.insert(0, contact)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_contact_added(self, name, email, resourceName, etag, error=''):
        if error:
            # TODO: Handle this error. Maybe, drop all data and then resync everything again.
            print("Couldn't add new contact. Error: ", error)
            raise Exception()

        _, topic, payload, contact = self.sync_helper.pull_event()
        ulid = contact.get('ulid')
        found = False
        for idx, con in enumerate(self._data):
            if con.get('ulid') == ulid:
                # TODO: If contact was modified, you will also have to update the resourceName of the payload
                if topic != 'add_contact':
                    # TODO: Update this when you add contact_modified topic to ContactEventChannel
                    pass
                # Contact might've been updated so just add resourceName and etag
                self._data[idx]['resourceName'] = resourceName
                self._data[idx]['etag'] = etag
                found = True
                break
        if found is False:
            # Contact was deleted, just update the resourceName of event payload in the event queue
            found = False
            for event in self.sync_helper.events():
                _, _, payload, contact = event
                if contact.get('ulid') == ulid:
                    payload['resourceName'] = resourceName
                    found = True
                    break
            # If found is False something really went wrong.
            assert found is True

        # Now send next event if there's any left in the queue
        self.sync_helper.push_next_event()
