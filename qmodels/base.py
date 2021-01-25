from PyQt5.QtCore import QAbstractListModel, Qt


class BaseListModel(QAbstractListModel):

    def __init__(self, data=None):
        super().__init__(None)
        self.page_length = 0  # page_length has to be set in concrete implementations

        self._data = data if data else []
        self.begin = 0
        self.end = min(self.page_length, len(self._data))
        self._displayed_data = self._data[self.begin:self.end]

        # Set to index of the last item, if you for sure know that's the real last item.
        self._last_item_idx = None

    def __len__(self):
        return len(self._data)

    def rowCount(self, parent=None):
        return len(self._displayed_data)

    def current_index(self):
        return self.begin, self.end

    def set_page_length(self, page_length):
        self.begin = 0
        self.end = min(page_length, len(self._data))
        self.page_length = page_length

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

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
                self.end = min(self.begin + self.page_length, len(self._data))
                self._displayed_data = self._data[self.begin:self.end]
            self.endResetModel()

    def replace_data(self, data):
        self.beginResetModel()
        self._data = data
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def load_next(self):
        if self.end == len(self._data):
            self.beginResetModel()
            self.endResetModel()
            return

        self.begin += self.page_length
        self.end = min(self.end + self.page_length, len(self._data))

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def load_previous(self):
        if self.begin == 0:
            self.beginResetModel()
            self.endResetModel()
            return

        self.end = self.begin
        self.begin = max(self.begin - self.page_length, 0)

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def remove_data(self, index):
        self._data.pop(index.row())
        self.end = min(self.begin + self.page_length, len(self._data))

        self.beginResetModel()
        self._displayed_data = self._data[self.begin:self.end]
        self.endResetModel()

    def is_last_page(self):
        if self._last_item_idx:
            return self.end == self._last_item_idx
        return False
