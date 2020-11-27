from PyQt5.QtCore import Qt

from qmodels.base import BaseListModel
from qmodels.options import options
from channels.event_channels import EmailEventChannel, OptionEventChannel
from datetime import datetime


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
        EmailEventChannel.publish('page_request', {'category': self.category})

    def data(self, index, role=Qt.DisplayRole):
        # TODO: Improve this, by splitting display text into 3 parts: Date, From, Snippet
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

    def emit_email_id(self, idx):
        EmailEventChannel.publish('email_request', {'category': 'email_content', 'value': self._displayed_data[idx].get('id')})

    def change_page_length(self, message):
        self.set_page_length(message.get('value'))

    def load_next_page(self):
        if self.end == len(self._data):
            self.fetching = True
            EmailEventChannel.publish('page_request', {'category': self.category})
            return

        self.load_next()

    def load_previous_page(self):
        self.load_previous()
