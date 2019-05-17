from viewmodels_mvvm._singleton import SingletonViewModel
from fetchers_mvvm.messages import MessageContentFetcher


class MessageContentViewModel(object, metaclass=SingletonViewModel):

    def __init__(self):
        self._srv = None


    def assign_service(self, service):
        self._srv = service

    def fetch_data(self, message_id):
        pass