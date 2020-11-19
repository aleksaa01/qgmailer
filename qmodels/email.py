from PyQt5.QtCore import QAbstractListModel, Qt

from qmodels.options import options
from channels.event_channels import EmailEventChannel, OptionEventChannel


class BaseListModel(QAbstractListModel):

    def __init__(self, data=None):
        super().__init__(None)
        self.page_length = None  # page_length has to be set in concrete implementations

        self._data = data if data else []
        self.begin = 0
        self.end = min(self.page_length, len(self._data))
        self._displayed_data = self._data[self.begin:self.end]

        # TODO: This is not a great system. Implement better one.
        # last_page flag should be set when model is at the last page.
        # This functionality should be implemented in concrete classes.
        self._last_page = False

    def rowCount(self, parent=None):
        return len(self._displayed_data)

    def current_index(self):
        return self.begin, self.end

    def set_page_length(self, page_length):
        self.begin = 0
        self.end = min(page_length, len(self._data))
        self.page_length = page_length
        self._last_page = False

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def is_last_page(self):
        """Concrete classes are responsible for setting _last_page flag"""
        return self._last_page

    def data(self, index, role=Qt.DisplayRole):
        raise NotImplementedError('data method is not implemented yet.')

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def create_data(self, data):
        # Use only if model is not set. Otherwise observing views won't be updated.
        self._data = data
        self._displayed_data = self._data[self.begin:self.end]

    def add_data(self, data, notify=True):
        # Adds data to already existing data, so model reset is required.
        if notify:
            self.beginResetModel()
        self._data += data
        if notify:
            # extend self.end if page length was smaller than self.page_length
            if self.end - self.begin < self.page_length:
                self.end = min(self.end + self.page_length, len(self._data))
                self._displayed_data = self._data[self.begin:self.end]
            self.endResetModel()

    def replace_data(self, data):
        self.beginResetModel()
        self._data = data
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def load_next(self):
        if self.end == len(self._data) or self._last_page is True:
            return

        self.begin += self.page_length
        self.end = min(self.end + self.page_length, len(self._data))

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def load_previous(self):
        if self.begin == 0:
            return

        self._last_page = False
        self.end = self.begin
        self.begin -= self.page_length

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def remove_data(self, index):
        self._data.pop(index.row())
        self.end = max(self.begin, self.end - 1)

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()


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
        if role == Qt.DisplayRole:
            return self._displayed_data[index.row()].get('snippet')

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
            if data is None:
                # No more data to load, set _last_page flag
                self._last_page = True
            else:
                self.add_data(message.get('value'), notify=False)
                self.load_next()

    def emit_email_id(self, idx):
        EmailEventChannel.publish('email_request', {'category': self.category, 'id': self._displayed_data[idx].get('id')})

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
