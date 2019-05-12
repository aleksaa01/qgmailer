from PyQt5.QtCore import QThread, Qt
from models.contacts import ContactsListModel
from googleapis.people.connection import PConnection
from fetchers_mvvm.contacts import ContactsFetcher


class CustomListModel(ContactsListModel):
    def __init__(self, data=None, parent=None):
        super().__init__(data, parent)

        self.current_page = 0
        self.last_page = 0

    def data(self, index, role=None):
        item = self._displayed_data[index.row()]
        if role == Qt.DisplayRole:
            return item.name + ': ' + item.email

    def addData(self, data):
        print('addData called')
        self.last_page += len(data) // self.PER_PAGE
        if self.current_page == 0:
            self.current_page = 1

        super().addData(data)

    def loadNext(self):
        print('loadNext Before:', self.current_page, self.last_page)
        self.current_page = min(self.current_page + 1, self.last_page)
        print('loadNext After:', self.current_page, self.last_page)
        super().loadNext()

    def loadPrevious(self):
        print('loadPrevious Before:', self.current_page, self.last_page)
        self.current_page = max(self.current_page - 1, 0)
        print('loadPrevious After:', self.current_page, self.last_page)
        super().loadPrevious()


class ContactsViewModel(object):

    def __init__(self):
        self.contacts_listmodel = CustomListModel()
        self._page_token = None

        self._on_loading_list = []
        self._on_loaded_list = []

    def run(self):
        # Slow methods go here.
        self._conn = PConnection()
        self._service = self._conn.acquire()
        self.fetcher = ContactsFetcher(self._service)
        self.fetcher.pageLoaded.connect(self.add_data)
        self.fetcher.threadFinished.connect(self._update_page_token)
        self.run_fetcher()

    def run_fetcher(self):
        self.fetcher.start()

    def _update_page_token(self, page_token):
        self._page_token = page_token

    def add_data(self, data):
        self.contacts_listmodel.addData(data)
        self.notify(self._on_loading_list)

    def load_next(self):
        # Not all pages might be fetched yet.
        if self.contacts_listmodel.current_page == self.contacts_listmodel.last_page:
            if self._page_token:
                self.notify(self._on_loading_list)
                self.run_fetcher()
                return
        self.contacts_listmodel.loadNext()

    def load_prev(self):
        self.contacts_listmodel.loadPrevious()

    def on_loaded(self, callback):
        self._on_loaded_list.append(callback)

    def on_loading(self, callback):
        self._on_loading_list.append(callback)

    def notify(self, lst):
        for callback in lst:
            callback()
