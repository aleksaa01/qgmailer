from PyQt5.QtCore import Qt

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import EmailEventChannel, OptionEventChannel
from channels.sync import SyncHelper


class EmailModel(BaseListModel):

    def __init__(self, category, data=None):
        super().__init__(data)

        self.page_length = options.emails_per_page
        self.category = category
        self.fetching = False

        EmailEventChannel.subscribe('page_response', self.add_new_page)
        OptionEventChannel.subscribe('emails_per_page', self.change_page_length)

        # Get first page
        self.fetching = True
        EmailEventChannel.publish('page_request', category=self.category)

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
            # TODO: Handle this error somehow.
            print("Page request failed... Error: ", error)
            raise Exception()
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

        # Last item checked is now stored in start
        print("Start index: ", start)
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
            EmailEventChannel.publish('page_request', category=self.category)
            return

        self.load_next()

    def load_previous_page(self):
        self.load_previous()

    def trash_email(self, idx):
        print(f"Removing email at index {idx}:", self.displayed_data[idx].get('email'))
        email = self.displayed_data[idx]
        topic = 'remove_email'
        payload = {'id': email.get('id'), 'from_ctg': self.category, 'to_ctg': ''}
        self.sync_helper.push_event(EmailEventChannel, topic, payload, email)

        self._data.pop(self.begin + idx)
        self.end = min(self.begin + self.page_length, len(self._data))
        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def handle_email_trashed(self, email, from_ctg, to_ctg, error=''):
        if from_ctg != self.category and to_ctg != self.category:
            return
        # TODO: Formatting of the email should be done in api service in api call function.
        if error:
            # TODO: Handle this error. Maybe, drop all data and then resync everything again.
            print("Failed to remove email...")
            raise Exception()

        if from_ctg == self.category:
            # This is the inbox model, so now we can remove the event
            self.sync_helper.pull_event()
            print(f"Email completely removed(category: {self.category}.")
            # Now send next event if there's any left in the queue
            self.sync_helper.push_next_event()
        elif to_ctg == self.category:
            # This is the trash model, so now we add it to model data
            self.add_data([email])
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
        if error:
            # TODO: Handle this error
            print("Failed to restore email")
            raise Exception()

        if self.category == from_ctg:
            self.sync_helper.pull_event()
            print(f"Email completely restored(category: {self.category}).")
            self.sync_helper.push_next_event()
        elif self.category == to_ctg:
            self.add_email(email)
