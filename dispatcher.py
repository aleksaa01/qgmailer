from GmailApi.connection import Connection
from GmailApi.fetch import ThreadsFetcher, MessagesFetcher
from models.threads import ThreadsListModel
from GmailApi.parser import extract_body
from PyQt5.QtCore import QTimer


class WebViewNotRegistered(Exception):
    pass


class Dispatcher(object):

    def __init__(self):
        self.connection = Connection()
        # dictionary content("key: value") = "threads_type: (resource, model)"
        self.dispatches = {}
        self._fetcher_list = []
        self.current_msg_fetcher = None
        self.web_view = None

    def register_webview(self, web_view_widget):
        self.web_view = web_view_widget

    def register_widget(self, widget, threads_type):
        if self.web_view is None:
            raise WebViewNotRegistered('Please register Web-view with '
                                       'dispatcher.register_webview(), before you register any other widget.')
        resource = self.connection.acquire()
        model = ThreadsListModel()
        widget.setModel(model)
        widget.clicked.connect(lambda index: self.item_clicked(index, threads_type))
        self.dispatches[threads_type] = [resource, model]

        fetcher = ThreadsFetcher(resource, threads_type)
        fetcher.pageLoaded.connect(lambda data: self.update_model(data, threads_type))
        fetcher.threadFinished.connect(lambda data: self.update_model(data, threads_type, True))
        self._fetcher_list.append(fetcher)

        print('Widget registered.')

    def register_widget_navigation(self, next_btn, prev_btn, threads_type):
        model = self.dispatches[threads_type][1]
        next_btn.clicked.connect(model.loadNext)
        prev_btn.clicked.connect(model.loadPrevious)

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
        resource = self.dispatches[threads_type][0]
        model = self.dispatches[threads_type][1]
        # Call set_webview_content and pass thread_Id and let it handle it.
        # Or, call some other method that will extract message ids,
        # call set_ and/or update_ on web_view
        self.set_webview_content(resource, model.extractId(index))

    def set_webview_content(self, resource, thread_id):
        # I am setting the Html first(with setHtml()), and then loading
        # the rest of the content using runJavaScript() because
        # setHtml is limited to 2 MB of data.
        self.web_view.setHtml('<html><body></body></html>')
        # Maybe you should make Message Handler class ?
        self.current_msg_fetcher = MessagesFetcher(resource, thread_id)
        self.current_msg_fetcher.threadFinished.connect(
            lambda messages: self.update_webview_content(resource, messages)
        )
        self.current_msg_fetcher.start()
        # Now append messages... So you ask HOW ?
        # Well, pass resource to MessagesFetcher, extract message ids.
        # pass message id to MessageFetcher or some other class.
        # then get back raw message(idk how, that's on you to implement),
        # and append it's content to Web-view using
        # self.update_webview_content, and in there you do:
        # self.web_view.runJavaScript('document.write(`{}`);'.format(message_content))

    def update_webview_content(self, resource, messages):
        # timer = QTimer()
        # timer.timeout.connect(lambda: self.append_webview_content())
        # timer.start(msec)
        for i in range(len(messages)):
            self.append_webview_content(extract_body(
                    resource.users().messages().get(id=messages[i]['id'], userId='me', format='raw').execute()
                )
            )

    def append_webview_content(self, content):
        self.web_view.runJavaScript('document.write(`{}`);'.format(content))
