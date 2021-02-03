from PyQt5.QtCore import Qt

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import EmailEventChannel, OptionEventChannel
from channels.signal_channels import SignalChannel
from services.sync import SyncHelper
from logs.loggers import default_logger

from json.decoder import JSONDecodeError
import json


LOG = default_logger()


class EmailModel(BaseListModel):

    on_error = SignalChannel(str, str)

    def __init__(self, category, data=None):
        super().__init__(data)

        self.page_length = options.emails_per_page
        self.category = category
        self.fetching = False

        EmailEventChannel.subscribe('page_response', self.add_new_page)
        EmailEventChannel.subscribe('email_trashed', self.handle_email_trashed)
        EmailEventChannel.subscribe('email_restored', self.handle_email_restored)
        EmailEventChannel.subscribe('email_sent', self.handle_email_sent)
        OptionEventChannel.subscribe('emails_per_page', self.change_page_length)

        # Get first page
        self.fetching = True
        EmailEventChannel.publish('page_request', category=self.category, max_results=self.page_length)

        self.sync_helper = SyncHelper()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._displayed_data[index.row()].get('email_field')

        elif role == Qt.DecorationRole:
            pass

        elif role == Qt.ToolTipRole:
            pass

    def current_index(self):
        if self.fetching:
            return None, None
        return self.begin, self.end

    def add_new_page(self, category, emails, error=''):
        if category != self.category:
            return

        if error:
            LOG.error(f"Page request failed... Error: {error}")
            self.on_error.emit(self.category, "Failed to load next page.")
            self.fetching = False
            return

        self.fetching = False

        if len(emails) == 0:
            self._last_item_idx = self.end

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

    def add_email(self, email):
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
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def emit_email_id(self, idx):
        EmailEventChannel.publish('email_request', email_id=self._displayed_data[idx].get('id'))

    def change_page_length(self, page_length):
        self.set_page_length(page_length)

    def load_next_page(self):
        if self.end == len(self._data):
            self.fetching = True
            EmailEventChannel.publish('page_request', category=self.category, max_results=self.page_length)
            return

        self.load_next()

    def load_previous_page(self):
        self.load_previous()

    def trash_email(self, idx):
        print(f"Moving email at index {idx} to trash:", self._displayed_data[idx].get('snippet'))
        email = self._displayed_data[idx]
        topic = 'trash_email'
        payload = {'email': email, 'from_ctg': self.category, 'to_ctg': ''}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_email_trashed(self, email, from_ctg, to_ctg, error=''):
        if from_ctg != self.category and to_ctg != self.category:
            return

        # Trying to move email to trash that was previously moved to trash won't produce an error.
        # But trying to move email to trash that was previously deleted will produce an error.
        if error:
            is_404 = _is_404_error(error)
            if not is_404:
                LOG.error(f"Failed to move the email to trash. Error: {error}")
                self.on_error.emit(self.category, "Failed to move the email to trash.")
            else:
                LOG.warning("Failed to move email to trash, it was already deleted.")
                self.on_error.emit(self.category, "Can't move that email to trash because it was already deleted.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        if from_ctg == self.category:
            # This is the inbox model, so now we can remove the event
            self.sync_helper.pull_event()
            print(f"Email sent to trash successfully(category): {self.category}.")
            # Now send next event if there's any left in the queue
            self.sync_helper.push_next_event()
        elif to_ctg == self.category:
            # This is the trash model, so now we add it to model data
            self.add_email(email)

    def restore_email(self, idx):
        print(f"Restoring email at index({idx}):", self._displayed_data[idx].get('snippet'))
        email = self._displayed_data[idx]
        topic = 'restore_email'
        payload = {'email': email, 'from_ctg': self.category, 'to_ctg': ''}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_email_restored(self, email, from_ctg, to_ctg, error=''):
        if from_ctg != self.category and to_ctg != self.category:
            return

        # Trying to restore already restored email won't produce an error.
        # But trying to restore previously deleted email will produce an error.
        if error:
            is_404 = _is_404_error(error)
            if not is_404:
                LOG.error(f"Failed to restore email. Error: {error}")
                self.on_error.emit(self.category, "Failed to restore the email.")
            else:
                LOG.warning("Failed to restore the email, it was already deleted.")
                self.on_error.emit(self.category, "Can't restore that email, because it was already deleted.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        if self.category == from_ctg:
            self.sync_helper.pull_event()
            print(f"Email completely restored(category: {self.category}).")
            self.sync_helper.push_next_event()
        elif self.category == to_ctg:
            self.add_email(email)

    def delete_email(self, idx):
        print(f"Deleting email at index {idx}", self._displayed_data[idx].get('snippet'))
        email = self._displayed_data[idx]
        topic = 'delete_email'
        payload = {'category': self.category, 'id': email.get('id')}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_email_deleted(self, category, error=''):
        if category != self.category:
            return

        # Trying to delete previously restored email won't produce an error, email will be deleted.
        # But trying to delete previously deleted email will produce an error.
        if error:
            is_404 = _is_404_error(error)
            if not is_404:
                LOG.error(f"Failed to delete email. Error: {error}")
                self.on_error.emit(self.category, "Failed to delete the email.")
            else:
                LOG.warning("Failed to delete the email, it was already deleted.")
                self.on_error.emit(self.category, "Can't delete that email, because it was already deleted.")

            self.sync_helper.pull_event()
            self.sync_helper.push_next_event()
            return

        self.sync_helper.pull_event()
        print("Email completely deleted.")
        self.sync_helper.push_next_event()

    def handle_email_sent(self, category, email, error=''):
        if self.category != category:
            return

        # Sending email to non existing email address won't produce an error.
        # You will just get email back from "Mail Devlivery Subsystem" saying "Address not found".
        if error:
            self.on_error.emit(self.category, "An error occurred, email wasn't sent.")
            LOG.error(f"Failed to send the email. Error: {error}")
            return

        self.add_email(email)


def _is_404_error(error):
    error_found = False
    try:
        if isinstance(error, str):
            error = json.loads(error)
        elif not isinstance(error, dict):
            raise ValueError('error must be either json string or json object(dict in python).')

        if error['error']['code'] == 404:
            error_found = True
    except (JSONDecodeError, KeyError):
        # error_found is initialized to False, so there's no need to set it here.
        pass

    return error_found
