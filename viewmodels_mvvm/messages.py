from PyQt5.QtCore import Qt

from models_mvvm.emails import PersonalEmailsModel, SocialEmailsModel, PromotionsEmailsModel, \
    UpdatesEmailsModel, SentEmailsModel, TrashEmailsModel
from models.threads import ThreadsListModel
from googleapis.gmail.connection import GConnection
from fetchers_mvvm.messages import MessagesFetcher



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
        print('addData called')
        self.last_page += 1
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


class MessagesViewModel(object):

    def __init__(self, messages_type):
        self._model = model_factory(messages_type)
        self.threads_listmodel = CustomListModel()
        self._page_token = None
        self._query = TYPE_TO_QUERY[messages_type]

    def run(self):
        """Put here any slow methods that might delay UI creating"""
        self._conn = GConnection()
        self._service = self._conn.acquire()
        self.fetcher = MessagesFetcher(self._service, self._query)
        self.fetcher.pageLoaded.connect(self.threads_listmodel.addData)
        self.fetcher.threadFinished.connect(self._update_page_token)
        self.run_fetcher()

    def run_fetcher(self, *args, **kwargs):
        self.fetcher.start()

    def _update_page_token(self, page_token):
        self._page_token = page_token

    def handle_ok(self):
        data = ['1', '2', '3', '4', '5']
        self._model.update([data])
        self.threads_listmodel.addData(data) # instead of addData, make new method "addPage"
        print(self._model.load())

    def handle_cancel(self):
        self._model.delete('1')
        self.threads_listmodel.replaceData([])
        print(self._model.load())

    def load_next(self):
        # Not all pages might be fetched yet.
        print('LOADING NEXT IN VIEWMODEL>>>', self.threads_listmodel.current_page, self.threads_listmodel.last_page)
        if self.threads_listmodel.current_page == self.threads_listmodel.last_page:
            if self._page_token:
                self.run_fetcher(page_token=self._page_token)
                return
        self.threads_listmodel.loadNext()

    def load_prev(self):
        print('LOADING PREVIOUS IN VIDEMODEL>>>', self.threads_listmodel.current_page, self.threads_listmodel.last_page)
        self.threads_listmodel.loadPrevious()