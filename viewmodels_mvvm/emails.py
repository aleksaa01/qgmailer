from viewmodels_mvvm._singleton import SingletonViewModel
from fetchers_mvvm.messages import MessageContentFetcher
from googleapis.gmail.gparser import extract_body
from googleapis.gmail.connection import GConnection
from googleapis.gmail.resources import ResourcePool


class EmailsViewModel(object, metaclass=SingletonViewModel):

    def __init__(self):
        self._fetcher = MessageContentFetcher()
        self._on_fetched_list = []
        self._fetcher.fetched.connect(lambda data: self.notify(self._on_fetched_list, data))
        self._resource_pool = ResourcePool(GConnection())

    def get_resource(self):
        return self._resource_pool.get()

    def fetch_data(self, message_id):
        resource = self.get_resource()
        self._fetcher.set_resource(resource, self._resource_pool.put)
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
