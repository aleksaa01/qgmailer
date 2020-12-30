from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListView, QVBoxLayout, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView

from qmodels.attachment import AttachmentListModel
from channels.event_channels import EmailEventChannel
from channels.signal_channels import SignalChannel

from os.path import splitext as split_extension
from base64 import urlsafe_b64decode


class AttachmentsController(object):
    def __init__(self, model):
        self.model = model

    def save_file(self, filepath, data):
        with open(filepath, 'wb') as f:
            f.write(urlsafe_b64decode(data))


class AttachmentsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = None
        self.c = None

        self.setFixedWidth(220)
        layout = QVBoxLayout()

        self.label = QLabel('Attachments')
        layout.addWidget(self.label)

        self.list_view = QListView()
        self.list_view.clicked.connect(self.save_attachment)
        layout.addWidget(self.list_view)

        self.setLayout(layout)

    def set_model(self, model):
        self._model = model
        self.list_view.setModel(model)
        self.c = AttachmentsController(model)

    def save_attachment(self, index):
        filename = self._model.emit_filename(index)
        payload = self._model.emit_attachments(index)

        name, extension = split_extension(filename)
        filepath, _ = QFileDialog.getSaveFileName(self, 'Save file', '/' + filename)

        self.c.save_file(filepath + extension, payload)

    def clear_attachments(self):
        self._model.clear_data()

    def append_attachments(self, attachments):
        self._model.add_data(attachments)

        # if there are no attachments just hide the ListView.
        if len(self._model) == 0:
            self.hide()
        elif self.isHidden():
            self.show()


class EmailViewerPageController(object):
    on_viewemail = SignalChannel(str, list)
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

        attachment_model = AttachmentListModel()
        self.attachments = AttachmentsView(self)
        self.attachments.set_model(attachment_model)
        layout.addWidget(self.attachments)

        self.setLayout(layout)

    def update_content(self, body, attachments):
        self.attachments.clear_attachments()
        self.email_page.runJavaScript(
            f'document.open(); document.write(""); document.write(`{body}`); document.close();'
        )

        self.attachments.append_attachments(attachments)

    def clear_content(self, flag):
        self.attachments.clear_attachments()
        self.email_page.runJavaScript('document.open(); document.write(""); document.close();')
