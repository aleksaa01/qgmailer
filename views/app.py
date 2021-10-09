from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QApplication, QLineEdit
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import QTimer

from views.icons import icons_rc
from views.managers import PageManagerView
from views.stylesheets import themes
from views.shortcuts import Shortcuts
from channels.event_channels import EmailEventChannel, ContactEventChannel, OptionEventChannel
from channels.signal_channels import SignalChannel
from services.api import APIService
from services.sync import EmailSynchronizer
from qmodels.options import options
from logs.loggers import default_logger


LOG = default_logger()


class AppController(object):
    on_themechanged = SignalChannel(str)
    on_fontsizechanged = SignalChannel(int)

    def __init__(self):
        OptionEventChannel.subscribe('theme', self.handle_theme_changed)
        OptionEventChannel.subscribe('font_size', self.handle_font_size_changed)

    def handle_theme_changed(self, theme):
        self.on_themechanged.emit(theme)

    def handle_font_size_changed(self, font_size):
        self.on_fontsizechanged.emit(font_size)


class AppView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.c = AppController()
        self.c.on_themechanged.connect(self.set_theme)
        self.c.on_fontsizechanged.connect(self.set_font_size)

        # TODO: Put shortcuts in page manager ???
        self.shortcuts = Shortcuts(self)

        self.api_service = APIService()

        EmailEventChannel.subscribe(
            'labels_request',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'labels_request', 'labels_sync', **kwargs)
        )

        EmailEventChannel.subscribe(
            'email_request',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'email_request', 'email_response', **kwargs)
        )
        EmailEventChannel.subscribe(
            'email_list_request',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'email_list_request', 'email_list_response', **kwargs)
        )
        EmailEventChannel.subscribe(
            'send_email',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'send_email', 'email_sent', **kwargs)
        )
        EmailEventChannel.subscribe(
            'trash_email',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'trash_email', 'email_trashed', **kwargs)
        )
        EmailEventChannel.subscribe(
            'restore_email',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'restore_email', 'email_restored', **kwargs)
        )
        EmailEventChannel.subscribe(
            'delete_email',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'delete_email', 'email_deleted', **kwargs)
        )
        EmailEventChannel.subscribe(
            'short_sync',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'short_sync', 'synced', **kwargs)
        )
        EmailEventChannel.subscribe(
            'modify_labels',
            lambda **kwargs: self.handle_request(EmailEventChannel, 'modify_labels', 'labels_modified', **kwargs)
        )
        ContactEventChannel.subscribe(
            'page_request',
            lambda **kwargs: self.handle_request(ContactEventChannel, 'page_request', 'page_response', **kwargs)
        )
        ContactEventChannel.subscribe(
            'remove_contact',
            lambda **kwargs: self.handle_request(ContactEventChannel, 'remove_contact', 'contact_removed', **kwargs)
        )
        ContactEventChannel.subscribe(
            'add_contact',
            lambda **kwargs: self.handle_request(ContactEventChannel, 'add_contact', 'contact_added', **kwargs)
        )
        ContactEventChannel.subscribe(
            'edit_contact',
            lambda **kwargs: self.handle_request(ContactEventChannel, 'edit_contact', 'contact_edited', **kwargs)
        )

        self.setWindowTitle('QGmailer')
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        win_width, win_height = options.resolution.split('x')
        self.resize(int(win_width), int(win_height))
        # This allows main window to be resized to the smallest possible size.
        # Instead of being limited(in minimum size) by layouts.
        self.setMinimumSize(1, 1)

        # cw - central widget
        self.cw = QWidget(self)

        self.page_manager = PageManagerView(parent=self.cw)

        mlayout = QHBoxLayout()
        mlayout.setContentsMargins(0, 0, 0, 0)
        mlayout.addWidget(self.page_manager)
        self.cw.setLayout(mlayout)
        self.set_theme(options.theme)
        self.set_font_size(options.font_size)
        self.setCentralWidget(self.cw)

        self.syncer = EmailSynchronizer.get_instance()
        self.timer = QTimer()
        self.timer.singleShot(1000 * 8, lambda: self.syncer.send_sync_request())
        self.timer.timeout.connect(lambda: self.syncer.send_sync_request())
        self.timer.start(1000 * 60)

    def handle_request(self, event_channel, from_topic, to_topic, **kwargs):
        callback = lambda api_event: self.handle_response(event_channel, to_topic, api_event)
        self.api_service.fetch(event_channel, from_topic, callback, **kwargs)

    def handle_response(self, event_channel, topic, api_event):
        try:
            event_channel.publish(topic, **api_event.payload)
        except Exception:
            LOG.error(
                "Error in AppView.handle_response(event_channel, topic, api_event.payload):"
                f"{event_channel}, {topic}, {api_event.payload}"
            )
            raise

    def set_theme(self, theme):
        LOG.info(f'Changing theme({theme})')
        self.cw.setStyleSheet(themes[theme])

    def set_font_size(self, font_size):
        LOG.info(f'Changing font size({font_size})')
        font = QFont()
        font.setPixelSize(font_size)
        QApplication.setFont(font)
        self.cw.setStyleSheet(self.cw.styleSheet())

    def closeEvent(self, event):
        self.hide()
        options.resolution = f'{str(self.width())}x{str(self.height())}'

        LOG.info("Shutting down the API service...")
        self.api_service.shutdown()
        LOG.info("Exiting main GUI loop...")
        event.accept()

    def mousePressEvent(self, event):
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            focused_widget.clearFocus()
        super().mousePressEvent(event)
