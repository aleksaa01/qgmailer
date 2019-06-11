from PyQt5.QtCore import QThread, Qt
from models.contacts import ContactsListModel
from googleapis.people.connection import PConnection
from fetchers.contacts import ContactsFetcher, CreateContactFetcher
from googleapis.people.contact_objects import ContactObject


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
        self.last_page += len(data) // self.per_page
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
        resource = self._conn.acquire()
        self.fetcher = ContactsFetcher(resource)
        self.fetcher.pageLoaded.connect(self.add_data)
        self.fetcher.threadFinished.connect(self._update_page_token)
        self.run_fetcher()

        self.create_contact_fetcher = CreateContactFetcher(resource)
        self.create_contact_fetcher.contact_created.connect(self.add_contact)

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

    def get_email(self, index):
        return self.contacts_listmodel.extractEmail(index)

    def create_contact(self, name, email):
        body = {'names': [{'givenName': name,'displayName': name}], 'emailAddresses': [{'value': email}]}
        self.create_contact_fetcher.set_body(body)
        self.create_contact_fetcher.start()

    def add_contact(self, contact_dict):
        contact = ContactObject(contact_dict)
        self.add_data([contact])

    def on_loaded(self, callback):
        self._on_loaded_list.append(callback)

    def on_loading(self, callback):
        self._on_loading_list.append(callback)

    def notify(self, lst):
        for callback in lst:
            callback()

    def set_page_length(self, new_length):
        self.contacts_listmodel.per_page = new_length
        self.contacts_listmodel.change_per_page()
