from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QHBoxLayout, QSpacerItem, \
    QLabel, QPushButton, QSizePolicy
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon, QPixmap

from views.context import ContactContext, InboxEmailContext, TrashEmailContext


class PageListController(object):

    def __init__(self, model):
        self.model = model

    def handle_previous(self):
        self.model.load_previous_page()

    def handle_next(self):
        self.model.load_next_page()

    def handle_click(self, idx):
        raise NotImplemented('handle_click is not implemented yet.')


# TODO: Implement loading progress sprite that will be shown when first or new page is getting fetched.
class PageListView(QWidget):
    on_itemclicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        # controller should be assigned in setModel
        self.c = None
        self._model = None

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
        self._model = model
        self.list_view.setModel(model)
        self.c = PageListController(model)

    def display_previous_page(self):
        self.c.handle_previous()

    def display_next_page(self):
        self.c.handle_next()

    def update_indexes(self):
        old_idx1, old_idx2 = self.page_index.indexes()
        idx1, idx2 = self._model.current_index()
        self.page_index.set_indexes(idx1, idx2)
        if idx1 == 0:
            self.page_index.enable_previous(False)
        else:
            self.page_index.enable_previous(True)
        if idx1 == old_idx1 and idx2 == old_idx2:
            self.page_index.enable_next(False)
        else:
            self.page_index.enable_next(True)

    def handle_click(self, qindex):
        self.c.handle_click(qindex.row())

    def show_context_menu(self, click_pos):
        raise NotImplemented('Classes that inherit from PageListView should implement show_context_menu.')


class InboxEmailListController(PageListController):

    def __init__(self, category, model):
        super().__init__(model)

        self.category = category

    def handle_click(self, idx):
        self.model.emit_email_id(idx)

    def trash_email(self, idx):
        if idx == -1:
            return
        self.model.trash_email(idx)


class InboxEmailListView(PageListView):

    def __init__(self, category, parent=None):
        super().__init__(parent=parent)

        self.category = category

    def set_model(self, model):
        self._model = model
        self.list_view.setModel(model)
        self.c = InboxEmailListController(self.category, model)
        self._model.modelReset.connect(self.update_indexes)
        self.page_index.set_indexes(*model.current_index())

    def show_context_menu(self, click_pos):
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = InboxEmailContext()
        callback = lambda: self.c.trash_email(self.list_view.indexAt(click_pos).row())
        context.on_trashed.connect(callback)
        context.show(menu_pos)
        context.on_trashed.disconnect(callback)


class TrashEmailListController(PageListController):

    def __init__(self, category, model):
        super().__init__(model)

        self.category = category

    def handle_click(self, idx):
        self.model.emit_email_id(idx)

    def restore_email(self, idx):
        if idx == -1:
            return
        self.model.restore_email(idx)

    def delete_email(self, idx):
        if idx == -1:
            return
        self.model.delete_email(idx)


class TrashEmailListView(PageListView):

    def __init__(self, category, parent=None):
        super().__init__(parent=parent)

        self.category = category

    def set_model(self, model):
        self._model = model
        self.list_view.setModel(model)
        self.c = TrashEmailListController(self.category, model)
        self._model.modelReset.connect(self.update_indexes)
        self.page_index.set_indexes(*model.current_index())

    def show_context_menu(self, click_pos):
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = TrashEmailContext()
        callback_restore = lambda: self.c.restore_email(self.list_view.indexAt(click_pos).row())
        callback_delete = lambda: self.c.delete_email(self.list_view.indexAt(click_pos).row())
        context.on_restored.connect(callback_restore)
        context.on_deleted.connect(callback_delete)
        context.show(menu_pos)
        context.on_restored.disconnect(callback_restore)
        context.on_deleted.disconnect(callback_delete)


class ContactListController(PageListController):

    def __init__(self, model):
        super().__init__(model)

    def handle_click(self, idx):
        self.model.emit_email(idx)

    def remove_contact(self, idx):
        if idx == -1:
            return
        self.model.remove_contact(idx)


class ContactListView(PageListView):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def set_model(self, model):
        self._model = model
        self.list_view.setModel(model)
        self.c = ContactListController(model)
        self._model.modelReset.connect(self.update_indexes)
        self.page_index.set_indexes(*model.current_index())

    def handle_click(self, qindex):
        idx = qindex.row()
        self.c.handle_click(idx)

    def show_context_menu(self, click_pos):
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = ContactContext()
        callback = lambda: self.c.remove_contact(self.list_view.indexAt(click_pos).row())
        context.on_removed.connect(callback)
        context.show(menu_pos)
        context.on_removed.disconnect(callback)


# TODO: Start index for lists should be 1 not 0. So for example, show 1-10 instead of 0-10.
# TODO: Replace next and previous QPushButton-s to QToolButton-s, and don't set object names...
class PageIndex(QWidget):

    on_next = pyqtSignal(bool)
    on_previous = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.horizontalLayout = QHBoxLayout(parent)
        self.horizontalLayout.setContentsMargins(5, 1, 5, 1)
        self.horizontalLayout.setSpacing(0)

        self.idx_start = 0
        self.idx_end = 0
        self.index_label = QLabel(f'{self.idx_start} - {self.idx_end}')
        self.horizontalLayout.addWidget(self.index_label)

        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)

        self.previous = QPushButton(parent)
        self.previous.setObjectName('personalPreviousBtn')
        self.previous.setMaximumSize(40, 40)
        self.previous.setCursor(QCursor(Qt.PointingHandCursor))
        self.previous.setText("")
        icon6 = QIcon()
        icon6.addPixmap(QPixmap(":/images/previous_button.png"), QIcon.Normal, QIcon.Off)
        self.previous.setIcon(icon6)
        self.previous.setIconSize(QSize(20, 20))
        self.previous.clicked.connect(lambda: self.on_previous.emit(True))
        self.horizontalLayout.addWidget(self.previous)

        self.next = QPushButton(parent)
        self.next.setObjectName('personalNextBtn')
        self.next.setMaximumSize(40, 40)
        self.next.setCursor(QCursor(Qt.PointingHandCursor))
        self.next.setText("")
        icon7 = QIcon()
        icon7.addPixmap(QPixmap(":/images/next_button.png"), QIcon.Normal, QIcon.Off)
        self.next.setIcon(icon7)
        self.next.setIconSize(QSize(20, 20))
        self.next.clicked.connect(lambda: self.on_next.emit(True))
        self.horizontalLayout.addWidget(self.next)

    def indexes(self):
        return self.idx_start, self.idx_end

    def set_indexes(self, idx1, idx2):
        self.idx_start = idx1
        self.idx_end = idx2
        self.index_label.setText(f'{idx1} - {idx2}')

    def enable_next(self, enable):
        self.next.setEnabled(enable)

    def enable_previous(self, enable):
        self.previous.setEnabled(enable)
