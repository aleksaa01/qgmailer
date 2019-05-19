from viewmodels_mvvm._singleton import SingletonViewModel
from fetchers_mvvm.messages import MessageContentFetcher
from googleapis.gmail.gparser import extract_body


class EmailsViewModel(object, metaclass=SingletonViewModel):

    def __init__(self):
        self._fetcher = MessageContentFetcher()
        self._on_fetched_list = []
        self._fetcher.fetched.connect(lambda data: self.notify(self._on_fetched_list, data))

    def assign_service(self, service):
        self._fetcher.set_service(service)

    def fetch_data(self, message_id):
        self._fetcher.set_message_id(message_id)
        self._fetcher.start()

    def on_fetched(self, callback):
        self._on_fetched_list.append(callback)

    def notify(self, callbacks, data):
        data = self._decode_data(data)
        for callback in callbacks:
            callback(data)

    def _decode_data(self, data):
        return extract_body(data)
