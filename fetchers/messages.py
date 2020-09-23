from PyQt5.QtCore import pyqtSignal, QThread
from googleapis.gmail.email_objects import MinimalMessage
from googleapis.gmail.requests import MessageRequest, MessageListRequest, BatchRequest

import time


CATEGORY_TO_QUERY = {
    'personal': 'in:personal',
    'social': 'in:social',
    'promotions': 'in:promotions',
    'updates': 'in:updates',
    'sent': 'in:sent',
    'trash': 'in:trash',
}

def fetch_message_list(resource, q, query, pages=2, page_len=100, page_token=None):
    def _batch_request_callback(request_id, response, exception=None):
        if exception:
            print("Error occured when fetching messages: {}".format(exception))
        idx = ord(request_id)
        msgs_page[idx] = MinimalMessage(response)

    # msglist_kwargs = {'userId': 'me', 'maxResults': self.page_len, 'q': self.query, 'pageToken': self.pt}
    # msglist_request = MessageListRequest(self.res_messages, self.release_callback)
    # msglist_request.set_kwargs(msglist_kwargs)
    page_token = page_token
    msglist_request = resource.users().messages().list(userId='me', maxResults=page_len, pageToken=page_token)
    headers = ['From', 'Subject']
    while pages > 0:
        msgs_resource = msglist_request.execute()

        # self.pt = msgs.get('nextPageToken', '')
        page_token = msgs_resource.get('nextPageToken', '')
        msgs_ids = msgs_resource.get('messages', [])
        msgs_page = [None] * len(msgs_ids)

        batch = resource.new_batch_http_request(_batch_request_callback)
        # msg_kwargs = {'userId': 'me', 'format': 'metadata', 'metadataHeaders': headers}
        # msg_request = MessageRequest(self.res_messages, self.release_callback, **msg_kwargs)
        for count, m in enumerate(msgs_ids):
            msg_request = resource.users().messages().get(id=m['id'], userId='me', format='metadata', metadataHeaders=headers)
            # Add request_id, which would be current index in messages_page in string.
            # Also pass None for callback, because I feel like Python just slows things
            # down when you pass him out of order kwargs, instead of full args.
            batch.add(msg_request, None, chr(count))
        # Looks like adding http object can help with performance (resource.http maybe ?)
        batch.execute()

        print('Page fetched... Query: {}'.format(query))
        q.put((resource, msgs_page))
        pages -= 1


class MessagesFetcher(QThread):

    pageLoaded = pyqtSignal(list)
    threadFinished = pyqtSignal(str)  # emits page token

    def __init__(self, resource1, resource2, release_callback, query, max_pages=0,
                 headers=None, msg_format='metadata', page_length=100, page_token=''):
        super().__init__(None)
        self.res_messages = resource1
        self.res_batch = resource2
        self.release_callback = release_callback
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
        session_pages = self.max_pages

        msglist_kwargs = {'userId': 'me', 'maxResults': self.page_len, 'q': self.query, 'pageToken': self.pt}
        msglist_request = MessageListRequest(self.res_messages, self.release_callback)
        msglist_request.set_kwargs(msglist_kwargs)
        while session_pages > 0:
            msgs = msglist_request.execute()

            self.pt = msgs.get('nextPageToken', '')
            messages_page = msgs.get('messages', [])
            self.msgs_page = [None] * len(messages_page)
            self.msg_count = 0

            batch = BatchRequest(self.res_batch, self._handle_batch_request)
            msg_kwargs = {'userId': 'me', 'format': self.msg_format, 'metadataHeaders': self.headers}
            msg_request = MessageRequest(self.res_messages, self.release_callback, **msg_kwargs)
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
