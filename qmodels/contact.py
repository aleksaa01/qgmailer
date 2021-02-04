from PyQt5.QtCore import Qt, pyqtSignal

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import ContactEventChannel, OptionEventChannel
from services.sync import SyncHelper
from logs.loggers import default_logger
from services.errors import is_404_error


LOG = default_logger()

# TODO: Another issue that might come up: How about removing a contact
#   in the middle of "page fetching process". Check if you have to adjust
#   begin and end attributes. Page processing will be blocked during this
#   so you don't have to worry about those kind of inconsistencies.


class ContactModel(BaseListModel):

    on_error = pyqtSignal(str)

    def __init__(self, data=None):
        super().__init__(data)

        self.page_length = options.contacts_per_page
        self.fetching = False

        ContactEventChannel.subscribe('page_response', self.add_new_page)
        ContactEventChannel.subscribe('contact_removed', self.handle_contact_removed)
        ContactEventChannel.subscribe('contact_added', self.handle_contact_added)
        ContactEventChannel.subscribe('contact_edited', self.handle_contact_edited)
        OptionEventChannel.subscribe('contacts_per_page', self.change_page_length)

        # Get first page
        self.fetching = True
        ContactEventChannel.publish('page_request', max_results=self.page_length)

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

        if len(contacts) == 0:
            self._last_item_idx = self.end

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
            ContactEventChannel.publish('page_request', max_results=self.page_length)
            return

        self.load_next()

    def load_previous_page(self):
        self.load_previous()

    def editable_data(self, idx):
        contact = self._displayed_data[idx]
        return contact.get('name'), contact.get('email')

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
        # Trying to remove a contact that was edited in the meantime won't produce an error.
        # Trying to remove a contact that was removed in the meantime will produce a 404 error.
        if error:
            is_404 = is_404_error(error)
            if not is_404:
                LOG.error(f"Failed to remove the contact. Error: {error}")
                self.on_error.emit("Failed to remove the contact.")
            else:
                LOG.warning("Failed to remove the contact, it was already removed.")
                self.on_error.emit("Can't remove that contact because it was already removed.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

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

        self._data.append(contact)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_contact_added(self, name, email, resourceName, etag, error=''):
        # If you fail to add a contact, you must remove the contact from the contact list,
        # and go through the event queue and remove all events that have the same contact ulid.
        # And don't forget to reset the model.
        if error:
            LOG.error(f"Failed to add the new contact. Error: {error}")
            self.on_error.emit("Failed to add the contact.")

            _, _, _, contact = self.sync_helper.pull_event()
            ulid = contact.get('ulid')
            # Remove contact from the list of contacts.
            for idx, con in enumerate(self._data):
                if con.get('ulid') == ulid:
                    self._data.pop(idx)
                    break
            # Remove any event that has the same ulid as the contact.
            for idx, event in enumerate(self.sync_helper.events()):
                _, _, _, con = event
                if con.get('ulid') == ulid:
                    self.sync_helper.remove_event(idx)
                    break

            self.beginResetModel()
            self._displayed_data = self._data[self.begin:self.end]
            self.endResetModel()
            self.sync_helper.push_next_event()
            return

        _, topic, payload, contact = self.sync_helper.pull_event()
        ulid = contact.get('ulid')
        found = False
        for idx, con in enumerate(self._data):
            if con.get('ulid') == ulid:
                # Add resourceName and etag to partial contact
                self._data[idx]['resourceName'] = resourceName
                self._data[idx]['etag'] = etag
                found = True
                break
        # NOTE: You still have to update event_queue in case contact was edited, because then
        #       both contact and event payload will have to be updated.
        # Contact was deleted, just update the resourceName and etag of event
        # payload in the event queue
        for event in self.sync_helper.events():
            _, _, payload, contact = event
            if contact.get('ulid') == ulid:
                payload['resourceName'] = resourceName
                payload['etag'] = etag
                found = True
                break
        # If found is False something really went wrong.
        assert found is True

        # Now send next event if there's any left in the queue
        self.sync_helper.push_next_event()

    def edit_contact(self, idx, name, email):
        print("Editing contact at index:", idx)
        contact = self._displayed_data[idx]
        if name == contact.get('name') and email == contact.get('email'):
            return

        topic = 'edit_contact'
        payload = {'name': name, 'email': email, 'resourceName': contact.get('resourceName', ''),
                   'etag': contact.get('etag', '')}
        self.sync_helper.push_event(ContactEventChannel, topic, payload, contact)

        contact['name'] = name
        contact['email'] = email
        self.beginResetModel()
        self.endResetModel()

    def handle_contact_edited(self, name, email, resourceName, etag, error=''):
        if error:
            # TODO: Handle this somehow
            print("Failed to edit the contact.")
            raise Exception()

        _, _, _, contact = self.sync_helper.pull_event()
        ulid = contact.get('ulid')
        found = False
        for idx, con in enumerate(self._data):
            if con.get('ulid') == ulid:
                # Update etag which will certainly change
                # I am not sure about name, email or resourceName, but I think they won't change
                self._data[idx]['etag'] = etag
                found = True
        # NOTE: What is someone edited the contact twice, that's why we have to go through
        #       all queued up events as well, and make sure they are updated will new information.
        #       Or if event was deleted of course, but that's more obvious.
        for event in self.sync_helper.events():
            _, _, payload, contact = event
            if contact.get('ulid') == ulid:
                payload['resourceName'] = resourceName
                payload['etag'] = etag
                found = True
                break
        # If found is False something really went wrong.
        assert found is True

        print("Contact successfully edited(name, email):", name, email)
        self.sync_helper.push_next_event()
