from PyQt5.QtCore import Qt

from qmodels.emails import PersonalEmailsModel, SocialEmailsModel, PromotionsEmailsModel, \
    UpdatesEmailsModel, SentEmailsModel, TrashEmailsModel
from qmodels.threads import ThreadsListModel
from googleapis.gmail.connection import GConnection
from googleapis.gmail.resources import ResourcePool
from googleapis.gmail.email_objects import trash_message
from fetchers.messages import MessagesFetcher

from collections import namedtuple


TYPE_TO_QUERY = {
    'personal': 'in:personal',
    'social': 'in:social',
    'promotions': 'in:promotions',
    'updates': 'in:updates',
    'sent': 'in:sent',
    'trash': 'in:trash',
}


def model_factory(message_type):
    type_to_model = {
        'personal': PersonalEmailsModel,
        'social': SocialEmailsModel,
        'promotions': PromotionsEmailsModel,
        'updates': UpdatesEmailsModel,
        'sent': SentEmailsModel,
        'trash': TrashEmailsModel,
    }

    clsmodel = type_to_model.get(message_type, None)
    if clsmodel is None:
        raise ValueError('Got unexisting message type: {}'.format(message_type))

    return clsmodel


class CustomListModel(ThreadsListModel):
    def __init__(self, data=None, parent=None):
        super().__init__(data, parent)

        self.current_page = 0
        self.last_page = 0

    def data(self, index, role=None):
        item = self._displayed_data[index.row()]
        from_field = getattr(item, 'from_field', 'Unknown')
        subject_field = getattr(item, 'subject_field', '(no subject)')
        if role == Qt.DisplayRole:
            return from_field + ': ' + subject_field

    def addData(self, data):
        print('addData method called')
        self.last_page += len(data) // self.per_page
        if self.current_page == 0:
            self.current_page = 1

        super().addData(data)

    def loadNext(self):
        self.current_page = min(self.current_page + 1, self.last_page)
        super().loadNext()

    def loadPrevious(self):
        self.current_page = max(self.current_page - 1, 0)
        super().loadPrevious()

    def changed_per_page(self):
        super().change_per_page()
        self.current_page = 0

    def removeData(self, index):
        print('REMOVING MESSAGE AT ROW:', index.row())
        super().removeData(index)
        self.last_page = self.rowCount() // self.per_page
        self.current_page = min(self.current_page, self.last_page)


class MessagesViewModel(object):

    def __init__(self, messages_type):
        self._model = model_factory(messages_type)
        self.threads_listmodel = CustomListModel()
        self._page_token = None
        self._query = TYPE_TO_QUERY[messages_type]
        self.resource_pool = None

        self._on_loading_list = []
        self._on_loaded_list = []

    def run(self):
        """Put here any slow methods that might delay UI creating"""
        gconn = GConnection()
        self.gmail_resource_pool = ResourcePool(gconn)
        resource1 = self.gmail_resource_pool.get()
        resource2 = self.gmail_resource_pool.get()
        self.fetcher = MessagesFetcher(resource1, resource2, self.gmail_resource_pool.put, self._query, 2)
        self.fetcher.pageLoaded.connect(self.add_data)
        self.fetcher.threadFinished.connect(self._update_page_token)
        self.fetcher.start()

    def add_data(self, data):
        self.threads_listmodel.addData(data)
        self.notify(self._on_loaded_list)

    def _update_page_token(self, page_token):
        self._page_token = page_token

    def load_next(self):
        # Not all pages might be fetched yet.
        print('Loading next page')
        if self.threads_listmodel.current_page == self.threads_listmodel.last_page:
            if self._page_token:
                self.notify(self._on_loading_list)
                self.fetcher.start()
                return
        self.threads_listmodel.loadNext()

    def load_prev(self):
        print('Loading previous page')
        self.threads_listmodel.loadPrevious()

    def extract_id(self, index):
        return self.threads_listmodel.extractId(index)

    def on_loading(self, callback):
        self._on_loading_list.append(callback)

    def on_loaded(self, callback):
        self._on_loaded_list.append(callback)

    def notify(self, lst):
        for callback in lst:
            callback()

    def set_page_length(self, new_length):
        self.threads_listmodel.per_page = new_length
        self.threads_listmodel.change_per_page()

    def actions(self):
        Action = namedtuple("Action", ["icon", "text", "callback"])

        actions = []
        actions.append(Action(None, "Remove", self.remove_message))

        return actions

    def remove_message(self, index):
        message_id = self.extract_id(index)
        self.threads_listmodel.removeData(index)
        resource = self.gmail_resource_pool.get()
        trash_message(resource, message_id)
        self.gmail_resource_pool.put(resource)
