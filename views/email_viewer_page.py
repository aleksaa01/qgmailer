from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListView, QVBoxLayout, QFileDialog, \
    QSplitter, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QSize

from qmodels.attachment import AttachmentListModel
from channels.event_channels import EmailEventChannel
from channels.signal_channels import SignalChannel
from views.dialogs import ErrorReportDialog

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

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel('Attachments')
        layout.addWidget(self.label)

        self.list_view = QListView()
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_view.setTextElideMode(Qt.ElideRight)
        self.list_view.clicked.connect(self.save_attachment)
        layout.addWidget(self.list_view)

        self.setLayout(layout)

    def sizeHint(self):
        return QSize(220, 0)

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
            self.on_viewemail.emit('', [], error)
            return
        self.on_viewemail.emit(body, attachments)

    def handle_email_request(self, message_id):
        self.on_clearview.emit(True)


class EmailViewerPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.c = EmailViewerPageController()
        self.c.on_viewemail.connect(self.update_content)
        self.c.on_clearview.connect(self.clear_content)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter()

        self._web_engine = QWebEngineView(self)
        self._web_engine.setMinimumWidth(330)
        self._web_engine.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.email_page = self._web_engine.page()
        self.splitter.addWidget(self._web_engine)

        attachment_model = AttachmentListModel()
        self.attachments = AttachmentsView(self)
        self.attachments.setMaximumWidth(300)
        self.attachments.set_model(attachment_model)
        self._attachments_collapsed = False
        self.splitter.addWidget(self.attachments)

        layout.addWidget(self.splitter)
        self.setLayout(layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # TODO: Fix the splitter not resizing when _web_engine gets smaller than minimumSize.
        #  Inspect sizes() for that, check if _web_engines size is less than minimumSize and
        #  somehow update the splitter's handle, it just has to be touched in order for it to resize
        #  to the proper size.
        #  !!! NOTE: First call to sizes returns [0, 0].
        page_size, attachments_size = self.splitter.sizes()
        if page_size == 0 and attachments_size == 0:
            return
        elif page_size < self._web_engine.minimumWidth() and not self._attachments_collapsed:
            self.splitter.setSizes((self.splitter.width(), 0))
            self._attachments_collapsed = True
        elif self._attachments_collapsed:
            splitter_width = self.splitter.width()
            size1 = self._web_engine.minimumWidth()
            size2 = self.attachments.sizeHint().width()
            if splitter_width > size1 + size2:
                self.splitter.setSizes((splitter_width - size2, size2))
                self._attachments_collapsed = False

    def update_content(self, body, attachments, error=None):
        if error:
            err_dialog = ErrorReportDialog(error)
            err_dialog.exec_()
            return

        self.attachments.clear_attachments()
        self.email_page.runJavaScript(
            f'document.open(); document.write(""); document.write(`{body}`); document.close();'
        )

        self.attachments.append_attachments(attachments)

    def clear_content(self, flag):
        self.attachments.clear_attachments()
        self.email_page.runJavaScript('document.open(); document.write(""); document.close();')
