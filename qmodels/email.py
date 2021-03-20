from PyQt5.QtCore import Qt

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import EmailEventChannel, OptionEventChannel
from channels.signal_channels import SignalChannel
from services.sync import SyncHelper, EmailSynchronizer
from logs.loggers import default_logger
from services.errors import get_error_code
from googleapis.gmail.labels import GMAIL_LABEL_UNREAD, LABEL_ID_SENT


LOG = default_logger()
EmailRole = Qt.UserRole + 100


class EmailModel(BaseListModel):

    on_error = SignalChannel(str, str)

    def __init__(self, label_id, data=None):
        super().__init__(data)

        self.page_length = options.emails_per_page
        self.label_id = label_id
        self.fetching = False

        EmailEventChannel.subscribe('page_response', self.add_new_page)
        EmailEventChannel.subscribe('email_trashed', self.handle_email_trashed)
        EmailEventChannel.subscribe('email_restored', self.handle_email_restored)
        EmailEventChannel.subscribe('email_deleted', self.handle_email_deleted)
        EmailEventChannel.subscribe('email_sent', self.handle_email_sent)
        EmailEventChannel.subscribe('total_messages', self.update_total_messages)
        OptionEventChannel.subscribe('emails_per_page', self.change_page_length)

        # Get first page
        self.fetching = True
        if label_id == LABEL_ID_SENT:
            EmailEventChannel.publish('page_request', label_id=label_id, max_results=self.page_length, headers=['To', 'Subject'])
        else:
            EmailEventChannel.publish('page_request', label_id=label_id, max_results=self.page_length)
        EmailEventChannel.publish('get_total_messages', label_id=label_id)

        self.sync_helper = SyncHelper()
        # Register this model to synchronizer in order to be able to receive short sync updates.
        EmailSynchronizer.get_instance().register(self, label_id)

    def data(self, index, role=Qt.DisplayRole):
        if role == EmailRole:
            return self._displayed_data[index.row()].get('email_field')

    def current_index(self):
        if self.fetching:
            return None, None
        return self.begin, self.end

    def add_new_page(self, label_id, emails, error=''):
        if label_id != self.label_id:
            return

        if error:
            LOG.error(f"Page request failed... Error: {error}")
            self.on_error.emit(self.label_id, "Failed to load next page.")
            self.fetching = False
            return

        self.fetching = False

        if self.end == 0:
            # Model is empty, just add data, don't load next page.
            self.add_data(emails)
        else:
            self.add_data(emails, notify=False)
            self.load_next()

    def add_data(self, data, notify=True):
        # Apply unique local IDs
        for row in data:
            row['ulid'] = self.sync_helper.new_ulid()
        super().add_data(data, notify)

    def insert_email(self, email):
        # Implement binary search and insert the email in last_element_index + 0/1,
        # depending on the value of internalDate of that last element.
        email_intd = int(email.get('internalDate'))
        start = 0
        end = len(self._data)
        while start < end:
            # integer overflow is not a problem in Python, so no need for "(end - start) // 2 + start"
            mid = (start + end) // 2
            intd = int(self._data[mid].get('internalDate'))
            if email_intd > intd:
                end = mid
            else:
                start = mid + 1

        # You have to create/update ulid, before you can insert it.
        email['ulid'] = self.sync_helper.new_ulid()
        # Last item checked is now stored in start
        self._data.insert(start, email)

        self.end = min(self.begin + self.page_length, len(self._data))
        self._total_items += 1
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def pop_email(self, email_id, raise_if_missing=False):
        matching_email = None
        for idx, email in enumerate(self._data):
            if email.get('id') == email_id:
                matching_email = self._data.pop(idx)
                break
        # TODO: We should probably empty sync_helper's event queue as well.

        if matching_email is None:
            if raise_if_missing is False:
                return None
            else:
                raise ValueError(f"Email with id: {email_id} doesn't exist.")

        self.end = min(self.begin + self.page_length, len(self._data))
        self._total_items -= 1
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

        return matching_email

    def find_email(self, email_id, internal_date=None):
        if internal_date is not None:
            start = 0
            end = len(self._data)
            while start < end:
                mid = (start + end) // 2
                email = self._data[mid]
                date = email.get('internalDate')
                # Emails are sorted in descending order, from biggest to lowest date.
                if internal_date > date:
                    end = mid
                elif internal_date < date:
                    start = mid + 1
                else:
                    assert email.get('id') == email_id
                    return mid
        else:
            for idx, email in enumerate(self._data):
                if email.get('id') == email_id:
                    return idx
        return -1

    def view_email(self, idx):
        email = self._displayed_data[idx]
        email_field = email.get('email_field')
        # Should we check labelIds here ?
        # In my opinion, there is no reason to do this, eventually we can even drop the use of labelIds.
        if email_field[-1] is True:
            email_field[-1] = False
            EmailEventChannel.publish('modify_labels', email_id=email.get('id'), to_add=(),
                                      to_remove=(GMAIL_LABEL_UNREAD,))
        EmailEventChannel.publish('email_request', email_id=email.get('id'))

    def change_page_length(self, page_length):
        self.set_page_length(page_length)

    def load_next_page(self):
        if self.end == len(self._data):
            self.fetching = True
            EmailEventChannel.publish('page_request', label_id=self.label_id, max_results=self.page_length)
            return

        self.load_next()

    def load_previous_page(self):
        self.load_previous()

    def trash_email(self, idx):
        LOG.info(f"Moving email at index {idx} to trash: {self._displayed_data[idx].get('snippet')}")
        email = self._displayed_data[idx]
        topic = 'trash_email'
        payload = {'email': email, 'from_lbl_id': self.label_id, 'to_lbl_id': 0}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self._total_items -= 1
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_email_trashed(self, email, from_lbl_id, to_lbl_id, error=''):
        if from_lbl_id != self.label_id and to_lbl_id != self.label_id:
            return

        # Trying to move email to trash that was previously moved to trash won't produce an error.
        # But trying to move email to trash that was previously deleted will produce an error.
        if error:
            # In case we are in the EmailModel for trashed emails, then we just return
            # cause there was an error, and we don't have to fix nor store anything.
            if to_lbl_id == self.label_id:
                return
            error_code = get_error_code(error)
            if error_code == 404:
                LOG.warning("Failed to move email to trash, it was already deleted.")
                self.on_error.emit(self.label_id, "Can't move that email to trash because it was already deleted.")
            else:
                LOG.error(f"Failed to move the email to trash. Error: {error}")
                self.on_error.emit(self.label_id, "Failed to move the email to trash.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        if from_lbl_id == self.label_id:
            # This is the inbox model, so now we can remove the event
            self.sync_helper.pull_event()
            LOG.info(f"Email sent to trash successfully(label_id): {self.label_id}")
            # Now send next event if there's any left in the queue
            self.sync_helper.push_next_event()
        elif to_lbl_id == self.label_id:
            # This is the trash model, so now we add it to model data
            self.insert_email(email)

    def restore_email(self, idx):
        LOG.info(f"Restoring email at index {idx}: {self._displayed_data[idx].get('snippet')}")
        email = self._displayed_data[idx]
        topic = 'restore_email'
        payload = {'email': email, 'from_lbl_id': self.label_id, 'to_lbl_id': 0}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self._total_items -= 1
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_email_restored(self, email, from_lbl_id, to_lbl_id, error=''):
        if from_lbl_id != self.label_id and to_lbl_id != self.label_id:
            return

        # Trying to restore already restored email won't produce an error.
        # But trying to restore previously deleted email will produce an error.
        if error:
            error_code = get_error_code(error)
            if error_code == 404:
                LOG.warning("Failed to restore the email, it was already deleted.")
                self.on_error.emit(self.label_id, "Can't restore that email, because it was already deleted.")
            else:
                LOG.error(f"Failed to restore email. Error: {error}")
                self.on_error.emit(self.label_id, "Failed to restore the email.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        if self.label_id == from_lbl_id:
            self.sync_helper.pull_event()
            LOG.info(f"Email completely restored(label_id: {self.label_id})")
            self.sync_helper.push_next_event()
        elif self.label_id == to_lbl_id:
            self.insert_email(email)

    def delete_email(self, idx):
        LOG.info(f"Deleting email at index {idx}: {self._displayed_data[idx].get('snippet')}")
        email = self._displayed_data[idx]
        topic = 'delete_email'
        payload = {'label_id': self.label_id, 'id': email.get('id')}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self._total_items -= 1
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_email_deleted(self, label_id, error=''):
        if label_id != self.label_id:
            return

        # Trying to delete previously restored email won't produce an error, email will be deleted.
        # But trying to delete previously deleted email will produce an error.
        if error:
            error_code = get_error_code(error)
            if error_code == 404:
                LOG.warning("Failed to delete the email, it was already deleted.")
                self.on_error.emit(self.label_id, "Can't delete that email, because it was already deleted.")
            else:
                LOG.error(f"Failed to delete email. Error: {error}")
                self.on_error.emit(self.label_id, "Failed to delete the email.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        self.sync_helper.pull_event()
        LOG.info("Email completely deleted.")
        self.sync_helper.push_next_event()

    def handle_email_sent(self, label_id, email, error=''):
        if self.label_id != label_id:
            return

        # Sending email to non existing email address won't produce an error.
        # You will just get email back from "Mail Devlivery Subsystem" saying "Address not found".
        if error:
            self.on_error.emit(self.label_id, "An error occurred, email wasn't sent.")
            LOG.error(f"Failed to send the email. Error: {error}")
            return

        self.insert_email(email)

    def update_total_messages(self, label_id, num_messages, error=''):
        if label_id != self.label_id:
            return
        if error:
            LOG.error(f"Failed to update total number of messages. Error: {error}.")
            return

        self._total_items = num_messages
