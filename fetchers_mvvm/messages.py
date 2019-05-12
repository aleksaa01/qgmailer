from PyQt5.QtCore import pyqtSignal, QThread
from googleapis.gmail.email_objects import MinimalMessage

import time


class MessagesFetcher(QThread):

    pageLoaded = pyqtSignal(list)
    threadFinished = pyqtSignal(str) # page token

    def __init__(self, service, query, max_pages=0, format='metadata',
                 headers=None, page_length=100, page_token=''):
        super().__init__(None)
        self.srv = service
        self.query = query
        self.max_pages = max_pages if max_pages > 0 else 1000
        self.format = format
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
