from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListView, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

from qmodels.attachment import AttachmentListModel
from channels.event_channels import EmailEventChannel
from channels.signal_channels import SignalChannel


class AttachmentViewer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedWidth(220)

        layout = QVBoxLayout()

        self.label = QLabel('Attachments')
        layout.addWidget(self.label)

        self.list_view = QListView()
        self.atcmod = AttachmentListModel()
        self.list_view.setModel(self.atcmod)
        layout.addWidget(self.list_view)

        self.list_view.clicked.connect(self.save_file)

        self.setLayout(layout)

    def save_file(self, index):
        # TODO: Implement "save file"
        # self.fileExtracted.emit(
        #     self.atcmod.extractFilename(index),
        #     self.atcmod.extractPayload(index)
        # )
        pass

    def clear_attachments(self):
        self.atcmod.clear_data()

    def append_attachments(self, attachments):
        self.atcmod.add_data(attachments)

        # if there are no attachments just hide the ListView.
        if len(self.atcmod) == 0:
            self.hide()
        elif self.isHidden():
            self.show()


class EmailViewerPageController(object):
    on_viewemail = SignalChannel(str, str)
    on_clearview = SignalChannel(bool)

    def __init__(self):
        EmailEventChannel.subscribe('email_response', self.handle_email_response)
        EmailEventChannel.subscribe('email_request', self.handle_email_request)

    def handle_email_response(self, body, attachments, error=''):
        if error:
            # TODO: Handle this error.
            print("Can't display an email. Error occured: ", error)
            raise Exception()
        self.on_viewemail.emit(body, attachments)

    def handle_email_request(self, email_id):
        self.on_clearview.emit(True)


class EmailViewerPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.c = EmailViewerPageController()
        self.c.on_viewemail.connect(self.update_content)
        self.c.on_clearview.connect(self.clear_content)

        layout = QHBoxLayout()

        self._web_engine = QWebEngineView(self)
        self.email_page = self._web_engine.page()
        layout.addWidget(self._web_engine)

        self.attachment_viewer = AttachmentViewer(self)
        layout.addWidget(self.attachment_viewer)

        self.setLayout(layout)

    def update_content(self, body, attachments):
        self.attachment_viewer.clear_attachments()
        self.email_page.runJavaScript(
            f'document.open(); document.write(""); document.write(`{body}`); document.close();'
        )

        self.attachment_viewer.append_attachments(attachments)

    def clear_content(self, flag):
        self.attachment_viewer.clear_attachments()
        self.email_page.runJavaScript('document.open(); document.write(""); document.close();')
