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
        ContactEventChannel.subscribe('contact_removed', self.handle_contact_removed)
        ContactEventChannel.subscribe('contact_added', self.handle_contact_added)
        OptionEventChannel.subscribe('contacts_per_page', self.change_page_length)

        # Get first page
        self.fetching = True
        ContactEventChannel.publish('page_request', {'category': self.category})

        self.event_queue = []
        # unique local ID, used internally for synchronization purposes
        self.ulid_counter = 0

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

        data = message.get('value')
        # apply unique local IDs
        for field in data:
            field['ulid'] = self.ulid_counter
            self.ulid_counter += 1

        if self.end == 0:
            # Model is empty, just add data, don't load next page.
            self.add_data(data)
        else:
            self.add_data(data, notify=False)
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
        print(f">>> Removing contact at index {idx}:", self._displayed_data[idx].get('email'))
        contact = self._displayed_data[idx]
        message = {'category': 'remove_contact', 'value': contact.get('resourceName')}
        # if event list is empty you can send the request, otherwise you have to wait
        # for the response to be processed until you can send another one.
        if len(self.event_queue) == 0:
            ContactEventChannel.publish(message.get('category'), message)
        self.event_queue.append((ContactEventChannel, message, contact))

        self._data.pop(self.begin + idx)
        self.end = self.begin + min(self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_contact_removed(self, message):
        if message.get('value').get('error'):
            print("Failed to remove contact...")
            # Maybe, drop all data and then sync again.
            return

        self.event_queue.pop(0) # remove associated request
        # Now send next event if there's any left in the queue
        if len(self.event_queue) > 0:
            event_channel, message, contact = self.event_queue[0]
            print(">>> Event queue is not empty, sending next event...", event_channel, message, contact)
            event_channel.publish(message.get('category'), message)

    def add_contact(self, name, email):
        print(f"Adding new contact(name, email): {name}, {email}")
        message = {'category': 'add_contact', 'value': {'name': name, 'email': email}}
        contact = {'name': name, 'email': email, 'ulid': self.ulid_counter}
        self.ulid_counter += 1

        if len(self.event_queue) == 0:
            ContactEventChannel.publish(message.get('category'), message)
        self.event_queue.append((ContactEventChannel, message, contact))

        self._data.insert(0, contact)
        self.end = self.begin + min(self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_contact_added(self, message):
        api_contact = message.get('value')
        if api_contact.get('error'):
            print("Failed to add contact...")
            # Maybe, drop all data and then sync again.
            return

        _, message, contact = self.event_queue.pop(0)
        ulid = contact.get('ulid')
        found = False
        for idx, con in enumerate(self._data):
            if con.get('ulid') == ulid:
                # TODO: If contact was modified, you will also have to update the value of the message
                if message.get('category') != 'add_contact':
                    # TODO: Update this when you add contact_modified topic to ContactEventChannel
                    pass
                # Contact might've been updated so just add resourceName and etag
                self._data[idx]['resourceName'] = api_contact.get('resourceName')
                self._data[idx]['etag'] = api_contact.get('etag')
                found = True
                break
        if found is False:
            # Contact was deleted, just update value of the event message in event queue
            found = False
            for event in self.event_queue:
                _, message, contact = event
                if contact.get('ulid') == ulid:
                    message['value'] = api_contact['resourceName']
                    found = True
                    break
            # If found is False something really went wrong.
            assert found is True

        # Now send next event if there's any left in the queue
        if len(self.event_queue) > 0:
            event_channel, message, contact = self.event_queue[0]
            print(">>> Event queue is not empty, sending next event...", event_channel, message, contact)
            event_channel.publish(message.get('category'), message)
