from PyQt5.QtCore import pyqtSignal, QThread
from googleapis.gmail.email_objects import MinimalMessage

import time


class MessagesFetcher(QThread):

    pageLoaded = pyqtSignal(list)
    threadFinished = pyqtSignal(str)  # emits page token

    def __init__(self, service, query, max_pages=0, msg_format='metadata',
                 headers=None, page_length=100, page_token=''):
        super().__init__(None)
        self.srv = service
        self.query = query
        self.max_pages = max_pages if max_pages > 0 else 1000
        self.format = msg_format
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
        session_pages = self.max_pages
        while session_pages > 0:
            msgs = self.srv.users().messages().list(
                userId='me', maxResults=self.page_len, q=self.query, pageToken=self.pt
            ).execute()

            self.pt = msgs.get('nextPageToken', '')
            messages_page = msgs.get('messages', [])
            self.msgs_page = [None] * len(messages_page)
            self.msg_count = 0

            batch = self.srv.new_batch_http_request(self._handle_batch_request)
            for m in messages_page:
                batch.add(self.srv.users().messages().get(
                    userId='me', id=m['id'], format=self.format, metadataHeaders=self.headers)
                )
            batch.execute()

            self.pageLoaded.emit(self.msgs_page)

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

    def __init__(self, message_id=None, service=None, msg_format='raw', parent=None):
        super().__init__(parent)

        self.message_id = message_id
        self.srv = service
        self.msg_format = msg_format

    def set_service(self, new_service):
        self.srv = new_service

    def set_message_id(self, new_message_id):
        self.message_id = new_message_id

    def run(self):
        msg_content = self.srv.users().messages().get(
            id=self.message_id, userId='me', format=self.msg_format).execute()
        self.fetched.emit(msg_content['raw'])

