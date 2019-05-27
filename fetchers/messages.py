from PyQt5.QtCore import pyqtSignal, QThread
from googleapis.gmail.email_objects import MinimalMessage
from googleapis.gmail.requests import MessageRequest, MessageListRequest, BatchRequest


import time


class MessagesFetcher(QThread):

    pageLoaded = pyqtSignal(list)
    threadFinished = pyqtSignal(str)  # emits page token

    def __init__(self, resource_pool, query, max_pages=0, headers=None, msg_format='metadata', page_length=100, page_token=''):
        super().__init__(None)
        self.resource_pool = resource_pool
        self.query = query
        self.max_pages = max_pages if max_pages > 0 else 1000
        self.msg_format = msg_format
        self.headers = headers if headers else ['From', 'Subject']
        self.page_len = page_length
        self.pt = page_token

        self.msgs_page = []
        self.msg_count = 0

    def run(self):
        print('Running MessagesFetcher...')
        t1 = time.perf_counter()
        self.session_pages = self.max_pages
        self._load()
        self.threadFinished.emit(self.pt)
        t2 = time.perf_counter()
        print('Fetched messages in {} seconds.'.format(t2 - t1))

    def _load(self):
        resource = self.resource_pool.get()
        session_pages = self.max_pages

        msglist_kwargs = {'userId': 'me', 'maxResults': self.page_len, 'q': self.query, 'pageToken': self.pt}
        msglist_request = MessageListRequest(resource, self.resource_pool.put)
        msglist_request.set_kwargs(msglist_kwargs)
        while session_pages > 0:
            msgs = msglist_request.execute()

            self.pt = msgs.get('nextPageToken', '')
            messages_page = msgs.get('messages', [])
            self.msgs_page = [None] * len(messages_page)
            self.msg_count = 0

            batch = BatchRequest(resource, self._handle_batch_request)
            msg_kwargs = {'userId': 'me', 'format': self.msg_format, 'metadataHeaders': self.headers}
            msg_request = MessageRequest(resource, self.resource_pool.put, **msg_kwargs)
            for m in messages_page:
                msg_request.update_kwargs('id', m['id'])
                batch.add(msg_request.build_request())
            batch.execute()

            self.pageLoaded.emit(self.msgs_page)

            msglist_request.update_kwargs('pageToken', self.pt)
            session_pages -= 1
            if not self.pt:
                break

    def _handle_batch_request(self, request_id, response, exception=None):
        if not response:
            return
        self.msgs_page[self.msg_count] = MinimalMessage(response)
        self.msg_count += 1


class MessageContentFetcher(QThread):

    fetched = pyqtSignal(str)

    def __init__(self, message_id=None, resource=None, release_callback=None, msg_format='raw', parent=None):
        super().__init__(parent)

        self.message_id = message_id
        self.res = resource
        self.msg_format = msg_format
        self.callback = release_callback

    def set_resource(self, resource, release_callback):
        self.res = resource
        self.callback = release_callback

    def set_message_id(self, new_message_id):
        self.message_id = new_message_id

    def run(self):
        kwargs = {'id': self.message_id, 'userId': 'me', 'format': self.msg_format}
        request = MessageRequest(self.res, self.callback, **kwargs)
        msg_content = request.execute()
        self.fetched.emit(msg_content['raw'])
        request.release()

