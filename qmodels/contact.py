from PyQt5.QtCore import Qt, pyqtSignal

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import ContactEventChannel, OptionEventChannel
from services.sync import SyncHelper
from logs.loggers import default_logger
from services.errors import get_error_code


LOG = default_logger()

# TODO: Another issue that might come up: How about removing a contact
#   in the middle of "page fetching process". Check if you have to adjust
#   begin and end attributes. Page processing will be blocked during this
#   so you don't have to worry about those kind of inconsistencies.

# TODO: All CRUD operations can potentially be made faster by making ulid=0 a special value
#   which marks ulid as invalid, which in turn allows us to check if contact is in the data
#   list just by checking if ulid==0 instead of going through the whole list.


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
        ContactEventChannel.publish('page_request')

        self.sync_helper = SyncHelper()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._displayed_data[index.row()].get('name')

    def current_index(self):
        if self.fetching:
            return None, None
        return self.begin, self.end

    def add_new_page(self, contacts, total_contacts, error=''):
        if error:
            LOG.error(f"Page request failed... Error: {error}")
            self.on_error.emit("Failed to load next page.")
            self.fetching = False
            return

        self.fetching = False

        self._total_items = total_contacts

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

    def editable_data(self, idx):
        contact = self._displayed_data[idx]
        return contact.get('name'), contact.get('email')

    def remove_contact(self, idx):
        LOG.info(f"Removing contact at index {idx}: {self._displayed_data[idx].get('email')}")
        contact = self._displayed_data[idx]
        topic = 'remove_contact'
        payload = {'resourceName': contact.get('resourceName')}
        # if event list is empty you can send the request, otherwise you have to wait
        # for the response to be processed until you can send another one.
        self.sync_helper.push_event(ContactEventChannel, topic, payload, contact)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self._total_items -= 1
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_contact_removed(self, error=''):
        # Trying to remove a contact that was edited in the meantime won't produce an error.
        # Trying to remove a contact that was removed in the meantime will produce a 404 error.
        if error:
            error_code = get_error_code(error)
            if error_code == 404:
                LOG.warning("Failed to remove the contact, it was already removed.")
                self.on_error.emit("Can't remove that contact because it was already removed.")
            else:
                LOG.error(f"Failed to remove the contact. Error: {error}")
                self.on_error.emit("Failed to remove the contact.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        # we got a successful response back, now remove the event
        self.sync_helper.pull_event()
        LOG.info("Contact completely removed.")
        # Now send next event if there's any left in the queue
        self.sync_helper.push_next_event()

    def add_contact(self, name, email):
        LOG.info(f"Adding new contact(name, email): {name}, {email}")
        topic = 'add_contact'
        payload = {'name': name, 'email': email}
        contact = {'name': name, 'email': email, 'ulid': self.sync_helper.new_ulid()}

        self.sync_helper.push_event(ContactEventChannel, topic, payload, contact)

        self._data.append(contact)
        self.end = min(self.begin + self.page_length, len(self._data))
        self._total_items += 1
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
                    self.end = min(self.begin + self.page_length, len(self._data))
                    break

            # Remove any event that has the same ulid as the contact.
            events = self.sync_helper.events()
            idx = 0
            while idx < len(events):
                _, topic, payload, con = events[idx]
                if con.get('ulid') == ulid:
                    self.sync_helper.remove_event(idx)
                else:
                    idx += 1

            self._total_items -= 1
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
                contact_to_update = self._data[idx]
                contact_to_update['resourceName'] = resourceName
                contact_to_update['etag'] = etag
                found = True
                break
        # NOTE: You still have to update event_queue in case contact was edited, because then
        #       both contact and event payload will have to be updated.
        # Contact was deleted, just update the resourceName and etag of event
        # payload in the event queue
        for event in self.sync_helper.events():
            _, topic, payload, contact = event
            if contact.get('ulid') == ulid:
                if topic == 'remove_contact':
                    # We don't do anything with etag or contact object in handle_contact_removed, so
                    # there is not need to update those fields in this case.
                    payload['resourceName'] = resourceName
                if topic == 'edit_contact':
                    # Update payload contact data.
                    payload_con = payload['contact']
                    payload_con['resourceName'] = resourceName
                    payload_con['etag'] = etag
                    # Update the contact object.
                    contact['resourceName'] = resourceName
                    contact['etag'] = etag
                found = True
        # If found is False something really went wrong.
        assert found is True

        # Now send next event if there's any left in the queue
        self.sync_helper.push_next_event()

    def edit_contact(self, idx, name, email):
        LOG.info("Editing contact at index:", idx)
        contact = self._displayed_data[idx]
        if name == contact.get('name') and email == contact.get('email'):
            LOG.info("Contact information wasn't changed. Returning immediately.")
            return

        topic = 'edit_contact'
        # Store new name, new email, and old contact(for reverting back to old name and email in case of failure)
        payload = {'name': name, 'email': email, 'contact': contact.copy()}
        self.sync_helper.push_event(ContactEventChannel, topic, payload, contact)

        contact['name'] = name
        contact['email'] = email
        self.beginResetModel()
        self.endResetModel()

    def handle_contact_edited(self, name, email, resourceName, etag, error=''):
        # Trying to edit a contact that was edited in the meantime will produce a 400 error.
        # In which case you have to update the contact before you can edit it.
        # Trying to edit a contact that was deleted in the meantime will produce a 404 error.
        if error:
            error_code = get_error_code(error)
            _, _, payload, contact = self.sync_helper.pull_event()
            ulid = contact.get('ulid')
            if error_code == 400:
                # Report error -> revert contact data -> remove all events associated with that contact.
                LOG.error(f"Failed to edit a contact. Error: {error}")
                self.on_error.emit("Can't edit that contact, because it was edited by someone else.")

                old_name = payload['contact']['name']
                old_email = payload['contact']['email']
                contact['name'] = old_name
                contact['email'] = old_email

                events = self.sync_helper.events()
                idx = 0
                while idx < len(events):
                    _, topic, payload, con = events[idx]
                    if con.get('ulid'):
                        self.sync_helper.remove_event(idx)
                    else:
                        idx += 1

            elif error_code == 404:
                # Report error -> remove contact -> remove all associated events -> reset UI.
                LOG.error(f"Failed to edit a contact. Error: {error}")
                self.on_error.emit("Can't edit that contact, because it was already deleted.")

                for idx, con in enumerate(self._data):
                    if con.get('ulid') == ulid:
                        self._data.pop(idx)
                        self.end = min(self.begin + self.page_length, len(self._data))
                        break

                events = self.sync_helper.events()
                idx = 0
                while idx < len(events):
                    _, topic, payload, con = events[idx]
                    if con.get('ulid'):
                        self.sync_helper.remove_event(idx)
                    else:
                        idx += 1

                self.beginResetModel()
                self._displayed_data = self._data[self.begin:self.end]
                self.endResetModel()
            else:
                LOG.error(f"Failed to edit the contact. Error: {error}")
                self.on_error.emit("Failed to edit the contact.")

            self.sync_helper.push_next_event()
            return

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
        #       all queued up events as well, and make sure they are updated with new information.
        #       Or if event was deleted of course, but that's more obvious.
        for event in self.sync_helper.events():
            _, topic, payload, contact = event
            if contact.get('ulid') == ulid:
                found = True
                if topic == 'edit_contact':
                    # We only need to update etag of the contact in the payload, because etag of the
                    # underlying contact has already been updated in the data list iteration. And we
                    # don't really use it in the intermediate steps, which means even if the contact
                    # was deleted and thus it's etag not updated, it's okay.
                    payload['contact']['etag'] = etag
                    # We break here, because there is no need to update other edit_contact events,
                    # because response to this event will update them anyways.
                    break
        # If found is False something really went wrong.
        assert found is True

        LOG.info("Contact successfully edited(name, email):", name, email)
        self.sync_helper.push_next_event()
