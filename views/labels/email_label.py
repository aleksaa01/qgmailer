from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from views.lists.lists import PageSlider, ResponsiveListView
from views.lists.delegates import EmailDelegate, SentEmailDelegate, TrashEmailDelegate
from views.dialogs import ErrorReportDialog
from views.context import EmailContext, TrashEmailContext


class EmailLabel(QWidget):
    """Generic email label. Inherit and override for specific functionality."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.label = None
        self.model = None

        mlayout = QVBoxLayout()
        mlayout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        self.page_slider = PageSlider(container)
        self.page_slider.on_previous.connect(self.previous_page)
        self.page_slider.on_next.connect(self.next_page)
        mlayout.addWidget(container)

        self.list_view = ResponsiveListView()
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_view.clicked.connect(self.email_clicked)
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)
        mlayout.addWidget(self.list_view)

        self.setLayout(mlayout)

    def set_model(self, label, model):
        self.label = label
        self.model = model
        self.model.modelReset.connect(self.update_indexes)
        self.update_indexes()
        delegate = self.get_delegate()
        self.list_view.setItemDelegate(delegate)
        self.list_view.setModel(self.model)

    def get_delegate(self):
        """Returns delegate for emails with generic(ones that don't need special painters) labels."""
        return EmailDelegate()

    def previous_page(self):
        self.model.load_previous_page()

    def next_page(self):
        # TODO: Disabling both buttons on next_page is not ideal, could implement something better.
        # Calling load_next_page on model might result in request fetching, that's why we disable
        # both buttons. After full response gets back update_indexes will be called and will enable
        # the buttons if necessary.
        self.page_slider.enable_previous(False)
        self.page_slider.enable_next(False)
        self.model.load_next_page()

    def update_indexes(self):
        idx_begin, idx_end = self.model.current_index()
        total_items = len(self.model)
        fully_loaded = self.model.fully_loaded
        page_length = self.model.page_length
        if idx_begin == 0:
            self.page_slider.enable_previous(False)
        else:
            self.page_slider.enable_previous(True)
        # FIXME: Ey yo what the hell ? So should we try to request another page if
        #  we get back a full response that's smaller than self.page_length(for example
        #  when we pop an email, request 1 email and insert an email before the request
        #  comes back. This is what happens during short sync !!!)
        if idx_end - idx_begin < page_length:
            self.page_slider.enable_next(False)
        elif idx_end == total_items - 1 and fully_loaded:
            self.page_slider.enable_next(False)
        else:
            self.page_slider.enable_next(True)

        # FIXME: I can pass label.total_messages here until fully_loaded is True, then
        #  len(model) Because len(model) might be different than label.total_messages
        self.page_slider.set_index_info(idx_begin, idx_end, total_items if fully_loaded else None)

    def email_clicked(self, qindex):
        self.model.view_email(qindex.row())

    def show_context_menu(self, click_pos):
        """Special email labels should override this method if they want special context menus."""
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = EmailContext()
        callback = lambda: self._trash_email(click_pos)
        context.on_trashed.connect(callback)
        context.show(menu_pos)
        context.on_trashed.disconnect(callback)

    def _trash_email(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        self.model.trash_email(idx)

    def display_error(self, label_id, error):
        # TODO: Should this be here ?
        if self.label.id != label_id:
            return

        dialog = ErrorReportDialog(error)
        dialog.exec_()


class SentEmailLabel(EmailLabel):

    def get_delegate(self):
        return SentEmailDelegate()


class TrashEmailLabel(EmailLabel):

    def get_delegate(self):
        return TrashEmailDelegate()

    def show_context_menu(self, click_pos):
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = TrashEmailContext()
        callback_restore = lambda: self._restore_email(click_pos)
        callback_delete = lambda: self._delete_email(click_pos)
        context.on_restored.connect(callback_restore)
        context.on_deleted.connect(callback_delete)
        context.show(menu_pos)
        context.on_restored.disconnect(callback_restore)
        context.on_deleted.disconnect(callback_delete)

    def _restore_email(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        self.model.restore_email(idx)

    def _delete_email(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        self.model.delete_email(idx)
