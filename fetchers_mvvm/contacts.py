from PyQt5.QtCore import pyqtSignal, QThread
from googleapis.people.contact_objects import ContactObject

import time


class ContactsFetcher(QThread):
    pageLoaded = pyqtSignal(list)
    threadFinished = pyqtSignal(str) # page token

    def __init__(self, service, fields=None, max_pages=0, page_length=100, page_token='', parent=None):
        super().__init__(parent)

        self.srv = service

        if fields:
            self.fields = fields
        else:
            self.fields = 'names,emailAddresses'

        self.max_pages = max_pages if max_pages > 0 else 10000
        self.page_len = page_length

        self.pt = page_token
        self.contacts = []

    def run(self):
        print('Running ContactsFetcher...')
        t1 = time.perf_counter()
        self._load()
        self.threadFinished.emit(self.pt)
        t2 = time.perf_counter()
        print('Fetched contacts in {} seconds:'.format(t2 - t1))

    def _load(self):
        session_pages = self.max_pages
        while session_pages > 0:
            page = self.srv.people().connections().list(
                resourceName='people/me',
                pageSize=self.page_len,
                pageToken=self.pt,
                personFields=self.fields).execute()

            contacts_page = page.get('connections', [])
            self.contacts = [None] * len(contacts_page)
            for index, contact_dict in enumerate(contacts_page):
                self.contacts[index] = ContactObject(contact_dict)

            self.pt = page.get('nextPageToken', '')

            self.pageLoaded.emit(self.contacts)

            session_pages -= 1
            if not self.pt:
                break
