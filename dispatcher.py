from googleapis.gmail.connection import GConnection
from googleapis.gmail.fetch import ThreadsFetcher, MessagesFetcher
from googleapis.gmail.send import EmailSender
from googleapis.people.connection import PConnection
from googleapis.people.fetch import ContactsFetcher
from models.threads import ThreadsListModel
from models.contacts import ContactsListModel

from PyQt5.QtCore import QTimer

from base64 import urlsafe_b64decode
import time

class EmailViewerNotRegistered(Exception):
    pass


class Dispatcher(object):

    def __init__(self):
        self.gconnection = GConnection()
        self.pconnection = PConnection()
        # dictionary content("key: value") = "item_type: (resource, model)"
        self.dispatches = {}
        self._fetcher_list = []

        self.email_viewer = None
        self.email_viewer_conn = self.gconnection.acquire()
        self.email_sender = EmailSender(self.gconnection.acquire())
        self.error_handler = None

    def register_email_viewer(self, email_viewer_widget):
        self.email_viewer = email_viewer_widget
        self.email_viewer.assign_resource(self.email_viewer_conn)

    def register_error_handler(self, error_handler):
        self.error_handler = error_handler

    def register_email_list(self, widget):
        if self.email_viewer is None:
            raise EmailViewerNotRegistered('Please register email viewer with '
                                           'dispatcher.register_email_viewer(), before you register any other widget.')

        item_type = widget.type

        resource = self.gconnection.acquire()
        model = ThreadsListModel()
        widget.model = model
        widget.link_items(lambda index: self.email_clicked(index, item_type))
        self.dispatches[item_type] = [resource, model]

        fetcher = ThreadsFetcher(resource, item_type)
        fetcher.pageLoaded.connect(lambda data: self.update_model(data, item_type))
        fetcher.threadFinished.connect(lambda data: self.update_model(data, item_type, True))
        fetcher.fetchError.connect(lambda message: self.error_handler(message))
        self._fetcher_list.append(fetcher)

    def register_contact_list(self, widget, reciver):
        item_type = widget.type if widget.type else 'contact'

        resource = self.pconnection.acquire()
        model = ContactsListModel()
        widget.model = model
        widget.link_items(lambda index: self.contact_clicked(index, item_type, reciver))
        self.dispatches[item_type] = [resource, model]

        fetcher = ContactsFetcher(resource)
        fetcher.pageLoaded.connect(lambda data: self.update_model(data, item_type))
        fetcher.threadFinished.connect(lambda data: self.update_model(data, item_type, True))
        fetcher.fetchError.connect(lambda message: self.error_handler(message))
        self._fetcher_list.append(fetcher)

    def start(self):
        self.t1 = time.perf_counter()
        self.counter = 0
        for fetcher in self._fetcher_list:
            fetcher.start()

    def update_model(self, data, item_type, replace=False):
        if replace is True:
            self.counter += 1
        if self.counter == len(self._fetcher_list):
            t2 = time.perf_counter()
            print('Time took:', t2 - self.t1)
        model = self.dispatches[item_type][1]
        if replace:
            model.replaceData(data)
        else:
            model.addData(data)

    def email_clicked(self, index, item_type):
        model = self.dispatches[item_type][1]
        self.set_email_viewer_content(model.extractId(index))

    def set_email_viewer_content(self, thread_id):
        self.current_msg_fetcher = MessagesFetcher(self.email_viewer_conn, thread_id)
        self.current_msg_fetcher.threadFinished.connect(self.email_viewer.update_content)
        self.current_msg_fetcher.start()

    def contact_clicked(self, index, item_type, receiver):
        model = self.dispatches[item_type][1]
        item_email = model.extractEmail(index)
        if not item_email:
            return
        current_text = receiver.text()
        if current_text:
            emails = current_text.split(',')
            if item_email not in emails:
                receiver.setText(current_text + ',' + item_email)
        else:
            receiver.setText(item_email)

    def send_email(self, to, subject, text):
        self.email_sender.send_email(to, subject, text)

    def save_file(self, filepath, file_content):
        with open(filepath, 'wb') as f:
            f.write(urlsafe_b64decode(file_content))
