from GmailApi.connection import Connection
from GmailApi.fetch import ThreadsFetcher, MessagesFetcher
from GmailApi.send import EmailSender
from models.threads import ThreadsListModel

from PyQt5.QtCore import QTimer

from base64 import urlsafe_b64decode


class EmailViewerNotRegistered(Exception):
    pass


class Dispatcher(object):

    def __init__(self):
        self.connection = Connection()
        # dictionary content("key: value") = "threads_type: (resource, model)"
        self.dispatches = {}
        self._fetcher_list = []

        self.email_viewer = None
        self.email_viewer_conn = self.connection.acquire()

        self.email_sender = EmailSender(self.connection.acquire())

    def register_email_viewer(self, email_viewer_widget):
        self.email_viewer = email_viewer_widget
        self.email_viewer.assign_resource(self.email_viewer_conn)

    def register_widget(self, widget):
        if self.email_viewer is None:
            raise EmailViewerNotRegistered('Please register email viewer with '
                                           'dispatcher.register_email_viewer(), before you register any other widget.')

        threads_type = widget.type

        resource = self.connection.acquire()
        model = ThreadsListModel()
        widget.model = model
        widget.link_email_list(lambda index: self.item_clicked(index, threads_type))
        self.dispatches[threads_type] = [resource, model]

        fetcher = ThreadsFetcher(resource, threads_type)
        fetcher.pageLoaded.connect(lambda data: self.update_model(data, threads_type))
        fetcher.threadFinished.connect(lambda data: self.update_model(data, threads_type, True))
        self._fetcher_list.append(fetcher)

    def start(self):
        for fetcher in self._fetcher_list:
            fetcher.start()

    def update_model(self, data, threads_type, replace=False):
        model = self.dispatches[threads_type][1]
        if replace:
            model.replaceData(data)
        else:
            model.addData(data)

    def item_clicked(self, index, threads_type):
        print('item_clicked called.')
        model = self.dispatches[threads_type][1]
        self.set_email_viewer_content(model.extractId(index))

    def set_email_viewer_content(self, thread_id):
        self.current_msg_fetcher = MessagesFetcher(self.email_viewer_conn, thread_id)
        self.current_msg_fetcher.threadFinished.connect(self.email_viewer.update_content)
        self.current_msg_fetcher.start()

    def send_email(self, to, subject, text):
        self.email_sender.send_email(to, subject, text)

    def save_file(self, filepath, file_content):
        with open(filepath, 'wb') as f:
            f.write(urlsafe_b64decode(file_content))
