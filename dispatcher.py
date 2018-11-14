from googleapis.gmail.connection import GConnection
from googleapis.gmail.fetch import ThreadsFetcher, MessagesFetcher
from googleapis.gmail.send import EmailSender
from models.threads import ThreadsListModel

from PyQt5.QtCore import QTimer

from base64 import urlsafe_b64decode


class EmailViewerNotRegistered(Exception):
    pass


class Dispatcher(object):

    def __init__(self):
        self.connection = GConnection()
        # dictionary content("key: value") = "item_type: (resource, model)"
        self.dispatches = {}
        self._fetcher_list = []

        self.email_viewer = None
        self.email_viewer_conn = self.connection.acquire()

        self.email_sender = EmailSender(self.connection.acquire())

    def register_email_viewer(self, email_viewer_widget):
        self.email_viewer = email_viewer_widget
        self.email_viewer.assign_resource(self.email_viewer_conn)

    def register_email_list(self, widget):
        if self.email_viewer is None:
            raise EmailViewerNotRegistered('Please register email viewer with '
                                           'dispatcher.register_email_viewer(), before you register any other widget.')

        item_type = widget.type

        resource = self.connection.acquire()
        model = ThreadsListModel()
        widget.model = model
        widget.link_items(lambda index: self.item_clicked(index, item_type))
        self.dispatches[item_type] = [resource, model]

        fetcher = ThreadsFetcher(resource, item_type)
        fetcher.pageLoaded.connect(lambda data: self.update_model(data, item_type))
        fetcher.threadFinished.connect(lambda data: self.update_model(data, item_type, True))
        self._fetcher_list.append(fetcher)

    def register_contact_list(self, widget, reciver):
        #item_type = widget.type

        #resource = self.connection.acquire()
        #model = ContactsListModel()
        #widget.model = model
        #widget.link_items(lambda index: self.item_clicked(index, item_type, reciver))
        #self.dispatches[item_type] = [resource, model]

        #fetcher =  ContactsFetcher(resource, item_type)
        #fetcher.pageLoaded.connect(lambda data: self.update_model(data, item_type))
        #fetcher.threadFinished.connect(lambda data: self.update_model(data, item_type, True))
        #self._fetcher_list.append(fetcher)
        pass

    def start(self):
        for fetcher in self._fetcher_list:
            fetcher.start()

    def update_model(self, data, item_type, replace=False):
        model = self.dispatches[item_type][1]
        if replace:
            model.replaceData(data)
        else:
            model.addData(data)

    def item_clicked(self, index, item_type):
        print('item_clicked called.')
        model = self.dispatches[item_type][1]
        self.set_email_viewer_content(model.extractId(index))

    def set_email_viewer_content(self, thread_id):
        self.current_msg_fetcher = MessagesFetcher(self.email_viewer_conn, thread_id)
        self.current_msg_fetcher.threadFinished.connect(self.email_viewer.update_content)
        self.current_msg_fetcher.start()

    def extract_emails(self, index, thread_type, receiver):
        # get model using item_type
        # get email from the model
        # add email to receiver
        pass

    def send_email(self, to, subject, text):
        self.email_sender.send_email(to, subject, text)

    def save_file(self, filepath, file_content):
        with open(filepath, 'wb') as f:
            f.write(urlsafe_b64decode(file_content))
