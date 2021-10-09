from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QHBoxLayout, QSpacerItem, \
    QLabel, QToolButton, QSizePolicy
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon, QPixmap

from views.lists.delegates import EmailDelegate
from views.context import ContactContext, EmailContext, TrashEmailContext
from views.dialogs import EditContactDialog, ErrorReportDialog


class ResponsiveListView(QListView):
    """
    List View that resizes its items depending on the width of the viewport.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wide_items = False

    def resizeEvent(self, event):
        recalc_layout = False

        viewport_width = self.viewport().width()
        if viewport_width > 700 and self.wide_items is True:
            self.wide_items = False
            delegate = self.itemDelegate()
            delegate.wide_items = False
            recalc_layout = True
        elif viewport_width <= 700 and self.wide_items is False:
            self.wide_items = True
            delegate = self.itemDelegate()
            delegate.wide_items = True
            recalc_layout = True

        super().resizeEvent(event)
        if recalc_layout:
            self.doItemsLayout()


# TODO: Implement loading progress sprite that will be shown when first or new page is getting fetched.
class PageListView(QWidget):
    on_itemclicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = None

        layout = QVBoxLayout()

        self.container = QWidget()
        self.container.setMinimumSize(0, 0)
        self.page_index = PageSlider(self.container)
        self.page_index.on_previous.connect(self.display_previous_page)
        self.page_index.on_next.connect(self.display_next_page)
        layout.addWidget(self.container)

        self.list_view = self.create_list_view()
        self.configure_list_view(self.list_view)

        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_view.clicked.connect(self.handle_click)
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_view)

        self.setLayout(layout)

    def create_list_view(self):
        """Overwrite this method if you need to use custom list views."""
        return QListView()

    def configure_list_view(self, list_view):
        """Use to apply list view specific configuration, that is not same for all list view types."""
        list_view.adjustSize()
        list_view.setUniformItemSizes(True)  # Enables Qt to do some optimizations.

    def set_model(self, model):
        self.model = model
        self.list_view.setModel(model)
        self.model.modelReset.connect(self.update_indexes)
        self.page_index.set_index_info(*model.current_index())

    def display_previous_page(self):
        self.model.load_previous_page()

    def display_next_page(self):
        self.model.load_next_page()

    def update_indexes(self):
        idx1, idx2 = self.model.current_index()
        total_items = len(self.model)
        self.page_index.set_index_info(idx1, idx2, total_items)

        if idx1 == 0:
            self.page_index.enable_previous(False)
        else:
            self.page_index.enable_previous(True)

        if total_items > 0 and total_items == idx2:
            self.page_index.enable_next(False)
        else:
            self.page_index.enable_next(True)

    def handle_click(self, qindex):
        raise NotImplemented('Classes that inherit from PageListView should implement handle_click.')

    def show_context_menu(self, click_pos):
        raise NotImplemented('Classes that inherit from PageListView should implement show_context_menu.')


class EmailListView(PageListView):

    def __init__(self, label_id, parent=None):
        super().__init__(parent=parent)

        self.label_id = label_id

    def handle_click(self, qindex):
        self.model.view_email(qindex.row())

    def set_model(self, model):
        super().set_model(model)
        model.on_error.connect(self.display_error)

    def create_list_view(self):
        return ResponsiveListView()

    def configure_list_view(self, list_view):
        delegate = EmailDelegate()
        list_view.setItemDelegate(delegate)

    def show_context_menu(self, click_pos):
        menu_pos = self.list_view.mapToGlobal(click_pos)
        context = EmailContext()
        callback = lambda: self.trash_email(click_pos)
        context.on_trashed.connect(callback)
        context.show(menu_pos)
        context.on_trashed.disconnect(callback)

    def trash_email(self, click_pos):
        idx = self.list_view.indexAt(click_pos).row()
        if idx == -1:
            return
        self.model.trash_email(idx)

    def display_error(self, label_id, error):
        if self.label_id != label_id:
            return
        dialog = ErrorReportDialog(error)
        dialog.exec_()


class TrashEmailListView(PageListView):

    def __init__(self, label_id, parent=None):
        super().__init__(parent=parent)

        self.label_id = label_id

    def handle_click(self, qindex):
        self.model.view_email(qindex.row())

    def set_model(self, model):
        super().set_model(model)
        model.on_error.connect(self.display_error)

    def create_list_view(self):
        return ResponsiveListView()

    def configure_list_view(self, list_view):
        delegate = EmailDelegate()
        list_view.setItemDelegate(delegate)

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

    def display_error(self, label_id, error):
        if self.label_id != label_id:
            return
        dialog = ErrorReportDialog(error)
        dialog.exec_()


class ContactListView(PageListView):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def handle_click(self, qindex):
        self.model.emit_email(qindex.row())

    def set_model(self, model):
        super().set_model(model)
        model.on_error.connect(self.display_error)

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

    def display_error(self, error):
        dialog = ErrorReportDialog(error)
        dialog.exec_()


class PageSlider(QWidget):

    on_next = pyqtSignal(bool)
    on_previous = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(parent)
        layout.setContentsMargins(5, 1, 5, 1)
        layout.setSpacing(4)

        self.index_label = QLabel('')
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

    def set_index_info(self, idx_begin, idx_end, total_items=None):
        if total_items is None:
            self.index_label.setText(f'{idx_begin} - {idx_end}  of  many')
        else:
            self.index_label.setText(f'{idx_begin} - {idx_end}  of  {total_items}')

    def enable_next(self, enable):
        self.next.setEnabled(enable)

    def enable_previous(self, enable):
        self.previous.setEnabled(enable)
