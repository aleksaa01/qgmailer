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

        for email in emails:
            email['ulid'] = self.sync_helper.new_ulid()

        if self.end == 0:
            # Model is empty, just add data, don't load next page.
            self.add_data(emails)
        else:
            self.add_data(emails, notify=False)
            self.load_next()

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
