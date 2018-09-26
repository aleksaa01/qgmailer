from PyQt5.QtCore import QThread, pyqtSignal
from html import unescape as html_unescape

PERSONAL_QUERY = 'category: personal'
SOCIAL_QUERY = 'category: social'
PROMOTIONS_QUERY = 'category: promotions'
UPDATES_QUERY = 'category: updates'
SENT_QUERY = 'in: sent'
TRASH_QUERY = 'in: trash'
SPAM_QUERY = 'in: spam'


QUERY_CATEGORIES = {
    'personal': PERSONAL_QUERY,
    'social': SOCIAL_QUERY,
    'promotions': PROMOTIONS_QUERY,
    'updates': UPDATES_QUERY,
    'sent': SENT_QUERY,
    'trash': TRASH_QUERY,
    'spam': SPAM_QUERY
}


class ThreadObject(object):

    def __init__(self, thread_dict):
        self.id = thread_dict['id']
        self.snippet = html_unescape(thread_dict['snippet'])
        self.historyId = thread_dict['historyId']


class ThreadsFetcher(QThread):
    """
    By default, fetching data from the API, but if filename is specified,
    data is loaded from that file.
    """
    threadFinished = pyqtSignal(list)
    pageLoaded = pyqtSignal(list)
    PAGE_LENGTH = 50

    def __init__(self, resource, query_type, filename='', parent=None):
        super().__init__(parent)

        self.res = resource
        self.threads = []

        matching_query = QUERY_CATEGORIES.get(query_type, False)
        if matching_query:
            self.query = matching_query
        else:
            raise KeyError('"query" must be in {}'.format(QUERY_CATEGORIES.keys()))

        self.filename = filename
        self.npt = ''
        self.num_pages = 0

    def run(self):
        print('Running thread...')
        if self.filename:
            self.load_from_file()

        self.npt = 'temp'
        self.load_from_api()

        self.threadFinished.emit(self.threads)

    def load_from_file(self):
        # Consider 3 approaches when making this method:
        # 1. loading from the json file(add parameter "json" maybe, or just "file_type" ?)
        # 2. loading from the encrypted storage(add parameter "key" maybe ?)
        # 3. maybe both ?
        raise NotImplemented('Method "load_from_file" is not yet implemented!')

    def load_from_api(self):
        while self.npt:
            self.num_pages += 1
            if self.num_pages == 1:
                page = self.res.users().threads().list(
                    userId='me', q=self.query,
                    maxResults=self.PAGE_LENGTH).execute()
            else:
                page = self.res.users().threads().list(
                    userId='me', q=self.query, pageToken=self.npt,
                    maxResults=self.PAGE_LENGTH).execute()

            for thread_dict in page.get('threads', []):
                self.threads.append(ThreadObject(thread_dict))
            self.npt = page.get('nextPageToken', '')

            if self.num_pages == 1:
                self.pageLoaded.emit(self.threads[:])

        print('{}(Number of threads, pages):'.format(
            self.query.capitalize()), len(self.threads), self.num_pages)


class MessagesFetcher(QThread):

    threadFinished = pyqtSignal(list)

    def __init__(self, resource, thread_id, format='minimal', filename='', parent=None):
        super().__init__(parent)

        self.res = resource
        self.thread_id = thread_id
        self.messages = []

        if format not in ('minimal', 'full', 'metadata'):
            raise KeyError('format must be either: minimal or full or metadata')
        self.format = format

        self.filename = filename

    def run(self):
        if self.filename:
            self.load_from_file()

        self.load_from_api()
        self.threadFinished.emit(self.messages)

    def load_from_file(self):
        raise NotImplemented('Method "load_from_file" is not yet implemented!')

    def load_from_api(self):
        msgs = self.res.users().threads().get(
            userId='me', id=self.thread_id, format=self.format).execute()

        self.messages.extend(msgs.get('messages', []))

        print('Number of messages(get type: {}):'.format(self.format), len(self.messages))
