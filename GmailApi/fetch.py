from os.path import splitext as split_extension
import datetime

from PyQt5.QtCore import QThread, pyqtSignal

from GmailApi.email_objects import ThreadObject
from GmailApi.email_objects import MessageObject
from options import Options


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


class BaseFetcher(QThread):

    threadFinished = pyqtSignal(list)
    ACCEPTABLE_FILETYPES = ('.json', '.p', '.pickle')

    def __init__(self, resource, filename='', parent=None):
        super().__init__(parent)

        self.res = resource
        if filename == '' or self._check_filetype(filename):
            self.filename = filename
        else:
            raise ValueError('Got filename with wrong file type'
                'Acceptable file types:', ', '.join(self.ACCEPTABLE_FILETYPES))

    def _check_filetype(self, filename):
        if split_extension(filename) in self.ACCEPTABLE_FILETYPES:
            return True
        return False

    def run(self):
        raise NotImplementedError('run is not implemented yet.')

    def load_from_api(self):
        raise NotImplementedError('load_from_api is not implemented yet.')

    def load_from_file(self):
        raise NotImplementedError('load_from_file is not implemented yet.')

class ThreadsFetcher(BaseFetcher):
    """
    By default, fetching data from the API, but if filename is specified,
    data is loaded from that file.
    """
    pageLoaded = pyqtSignal(list)
    PAGE_LENGTH = Options.app_options['threads_per_page']

    def __init__(self, resource, query_type, filename='', parent=None):
        super().__init__(resource, filename, parent)

        Options.optionsChanged.connect(self.change_page_length)

        self.threads = []

        matching_query = QUERY_CATEGORIES.get(query_type, False)
        if not matching_query:
            raise KeyError(
                'Query type: {}, is not in acceptable query types: {}'.format(
                    query_type, QUERY_CATEGORIES.keys()
                )
            )
        self.query = matching_query

        self.npt = ''
        self.num_pages = 0

    def run(self):
        print('Running thread...')
        if self.filename:
            self.load_from_file()
        else:
            self.npt = 'temp'
            self.load_from_api()

        self.threadFinished.emit(self.threads)

    def load_from_file(self):
        # Consider 3 approaches when making this method:
        # 1. loading from the json file(add parameter "json" maybe, or just "file_type" ?)
        # 2. loading from the encrypted storage(add parameter "key" maybe ?)
        # 3. maybe both ?
        super().load_from_file()

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

    def change_page_length(self):
        self.PAGE_LENGTH = Options.app_options['threads_per_page']


class MessagesFetcher(BaseFetcher):

    PAGE_LENGTH = Options.app_options['messages_per_page']

    def __init__(self, resource, thread_id=None, get_format='minimal', filename='', expire=None, parent=None):
        super().__init__(resource, filename, parent)

        self.thread_id = thread_id
        self.messages = []

        if get_format not in ('minimal', 'full', 'metadata'):
            raise KeyError('format must be either: minimal or full or metadata')
        self.format = get_format

        self.expire_date = None

        # expire should be in days
        if expire:
            self.expire_date = datetime.datetime.now() - datetime.timedelta(days=expire)

    def run(self):
        if self.filename:
            self.load_from_file()
        else:
            self.load_from_api()
        self.threadFinished.emit(self.messages)

    def load_from_api(self):
        if self.thread_id:
            self.load_threads()
        else:
            self.load_messages()

        print('Number of messages(get type: {}):'.format(self.format), len(self.messages))

    def load_threads(self):
        msgs = self.res.users().threads().get(
            userId='me', id=self.thread_id, format=self.format).execute()

        self.messages = [MessageObject(msg) for msg in msgs.get('messages', [])]

    def load_messages(self):
        npt = 'temp'
        num_pages = 0

        while npt:
            num_pages += 1
            if num_pages == 1:
                msgs = self.res.users().messages().list(
                    userId='me', maxResults=self.PAGE_LENGTH).execute()
            else:
                msgs = self.res.users().messages().list(
                    userId='me', pageToken=npt,
                    maxResults=self.PAGE_LENGTH).execute()

            batch = self.res.new_batch_http_request(self._handle_batch_request)
            for m in msgs['messages']:
                batch.add(self.res.users().messages().get(userId='me', id=m['id'], format='minimal'))
            batch.execute()

            if self.messages[-1].internalDate < self.expire_date:
                self._trim_expired()
                return

            npt = msgs.get('nextPageToken', '')

    def _handle_batch_request(self, request_id, response, exception=None):
        self.messages.append(MessageObject(response))

    def _trim_expired(self):
        index = len(self.messages) - self.PAGE_LENGTH
        while index < len(self.messages):
            if self.messages[index].internalDate < self.expire_date:
                del self.messages[index]
            else:
                index += 1

    def change_page_pength(self):
        self.PAGE_LENGTH = Options.app_options['messages_per_page']
