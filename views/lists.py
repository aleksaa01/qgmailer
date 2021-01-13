from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QHBoxLayout, QSpacerItem, \
    QLabel, QToolButton, QSizePolicy
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon, QPixmap

from views.context import ContactContext, InboxEmailContext, TrashEmailContext
from views.dialogs import EditContactDialog


# TODO: Implement loading progress sprite that will be shown when first or new page is getting fetched.
class PageListView(QWidget):
    on_itemclicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = None

        layout = QVBoxLayout()

        self.container = QWidget()
        self.container.setMinimumSize(0, 0)
        self.page_index = PageIndex(self.container)
        self.page_index.on_previous.connect(self.display_previous_page)
        self.page_index.on_next.connect(self.display_next_page)
        layout.addWidget(self.container)

        self.list_view = QListView()
        # self.list_view.mousePressEvent = self.mousePressEvent
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # adjustSize() - Adjusts the size of the widget to fit its contents.
        # This function uses sizeHint() if it is valid, i.e., the size hint's width and height are >= 0.
        # Otherwise, it sets the size to the children rectangle that covers all child widgets
        # (the union of all child widget rectangles).
        self.list_view.adjustSize()
        self.list_view.setUniformItemSizes(True)  # Enables Qt to do some optimizations.
        self.list_view.clicked.connect(self.handle_click)
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_view)

        self.setLayout(layout)

    def set_model(self, model):
        self.model = model
        self.list_view.setModel(model)
        self.model.modelReset.connect(self.update_indexes)
        self.page_index.set_indexes(*model.current_index())

    def display_previous_page(self):
        self.model.load_previous_page()

    def display_next_page(self):
        self.model.load_next_page()

    def update_indexes(self):
        old_idx1, old_idx2 = self.page_index.indexes()
        idx1, idx2 = self.model.current_index()
        total_length = len(self.model)
        self.page_index.set_indexes(idx1, idx2)
        if idx1 == 0:
            self.page_index.enable_previous(False)
        else:
            self.page_index.enable_previous(True)
        if idx1 == old_idx1 and idx2 == old_idx2 and idx2 == total_length:
            self.page_index.enable_next(False)
        else:
            self.page_index.enable_next(True)

    def handle_click(self, qindex):
        raise NotImplemented('Classes that inherit from PageListView should implement handle_click.')

    def show_context_menu(self, click_pos):
        raise NotImplemented('Classes that inherit from PageListView should implement show_context_menu.')


class EmailListView(PageListView):

    def __init__(self, category, parent=None):
        super().__init__(parent=parent)

        self.category = category

    def handle_click(self, qindex):
        self.model.emit_email_id(qindex.row())

    def show_context_menu(self, click_pos):
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = InboxEmailContext()
        callback = lambda: self.trash_email(click_pos)
        context.on_trashed.connect(callback)
        context.show(menu_pos)
        context.on_trashed.disconnect(callback)

    def trash_email(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        self.model.trash_email(idx)


class TrashEmailListView(PageListView):

    def __init__(self, category, parent=None):
        super().__init__(parent=parent)

        self.category = category

    def handle_click(self, qindex):
        self.model.emit_email_id(qindex.row())

    def show_context_menu(self, click_pos):
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = TrashEmailContext()
        callback_restore = lambda: self.restore_email(click_pos)
        callback_delete = lambda: self.delete_email(click_pos)
        context.on_restored.connect(callback_restore)
        context.on_deleted.connect(callback_delete)
        context.show(menu_pos)
        context.on_restored.disconnect(callback_restore)
        context.on_deleted.disconnect(callback_delete)

    def restore_email(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        self.model.restore_email(idx)

    def delete_email(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        self.model.delete_email(idx)


class ContactListView(PageListView):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def handle_click(self, qindex):
        self.model.emit_email(qindex.row())

    def show_context_menu(self, click_pos):
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = ContactContext()
        callback_remove = lambda: self.remove_contact(click_pos)
        callback_edit = lambda: self.edit_contact(click_pos)
        context.on_removed.connect(callback_remove)
        context.on_edit.connect(callback_edit)
        context.show(menu_pos)
        context.on_removed.disconnect(callback_remove)
        context.on_edit.disconnect(callback_edit)

    def remove_contact(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        self.model.remove_contact(idx)

    def edit_contact(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        name, email = self.model.editable_data(idx)
        dialog = EditContactDialog(name, email)
        dialog.contact_edited.connect(lambda name, email: self.model.edit_contact(idx, name, email))
        dialog.exec_()


class PageIndex(QWidget):

    on_next = pyqtSignal(bool)
    on_previous = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(parent)
        layout.setContentsMargins(5, 1, 5, 1)
        layout.setSpacing(4)

        self.idx_start = 0
        self.idx_end = 0
        self.index_label = QLabel()
        self.set_text(self.idx_start, self.idx_end)
        layout.addWidget(self.index_label)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer)

        self.previous = QToolButton(parent)
        self.previous.setObjectName('PageIndexButton')
        self.previous.setMaximumSize(40, 40)
        self.previous.setCursor(QCursor(Qt.PointingHandCursor))
        icon6 = QIcon()
        icon6.addPixmap(QPixmap(":/images/previous_button.png"), QIcon.Normal, QIcon.Off)
        self.previous.setIcon(icon6)
        self.previous.setIconSize(QSize(18, 18))
        self.previous.clicked.connect(lambda: self.on_previous.emit(True))
        layout.addWidget(self.previous)

        self.next = QToolButton(parent)
        self.next.setObjectName('PageIndexButton')
        self.next.setMaximumSize(40, 40)
        self.next.setCursor(QCursor(Qt.PointingHandCursor))
        icon7 = QIcon()
        icon7.addPixmap(QPixmap(":/images/next_button.png"), QIcon.Normal, QIcon.Off)
        self.next.setIcon(icon7)
        self.next.setIconSize(QSize(18, 18))
        self.next.clicked.connect(lambda: self.on_next.emit(True))
        layout.addWidget(self.next)

    def indexes(self):
        return self.idx_start, self.idx_end

    def set_indexes(self, idx1, idx2):
        if idx1 is None and idx2 is None:
            idx1, idx2 = 0, 0
        self.idx_start = idx1
        self.idx_end = idx2
        self.set_text(idx1, idx2)

    def set_text(self, idx1, idx2):
        if not (idx1 == 0 and idx2 == 0):
            idx1 += 1
        self.index_label.setText(f'{idx1} - {idx2}')

    def enable_next(self, enable):
        self.next.setEnabled(enable)

    def enable_previous(self, enable):
        self.previous.setEnabled(enable)
