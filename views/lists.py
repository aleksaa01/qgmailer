from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QHBoxLayout, QMenu, QSpacerItem, \
    QLabel, QPushButton, QSizePolicy
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QModelIndex
from PyQt5.QtGui import QCursor, QIcon, QPixmap


class PageListController(object):

    def __init__(self, model):
        self.model = model

    def handle_previous(self):
        self.model.load_previous_page()

    def handle_next(self):
        self.model.load_next_page()


class PageListView(QWidget):
    on_itemclicked = pyqtSignal(object)

    def __init__(self, actions, size=tuple(), parent=None):
        super().__init__(parent)

        if not isinstance(size, tuple):
            raise TypeError('Size must be a tuple: (width, height)')

        # controller should be assigned in setModel
        self.c = None
        self._model = None

        self.actions = actions

        # default size
        if not parent:
            self.width = 900
            self.height = 550

        if size and isinstance(size, tuple):
            self.width = size[0]
            self.height = size[1]
            self.setMinimumSize(size[0], size[1])

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

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.RightButton:
    #         # setup action menu
    #         action_menu = QMenu()
    #         action_map = {}
    #         for action in self.actions:
    #             if action.icon:
    #                 ret_action = action_menu.addAction(action.icon, action.text)
    #             else:
    #                 ret_action = action_menu.addAction(action.text)
    #             action_map[ret_action] = action
    #         chosen_action = action_menu.exec_(self.list_view.mapToGlobal(event.pos()))
    #         if chosen_action is None:
    #             return
    #         action = action_map[chosen_action]
    #         index = self.list_view.indexAt(event.pos())
    #         action.callback(index)
    #     else:
    #         index = self.list_view.indexAt(event.pos())
    #         # Get the data from the model(email id, etc. and emit that instead)
    #         return self.on_itemclicked.emit(index)


class EmailListController(PageListController):

    def __init__(self, category, model):
        super().__init__(model)

        self.category = category


class EmailListView(PageListView):

    def __init__(self, category, actions, parent=None):
        super().__init__(actions, parent=parent)

        self.category = category

    def set_model(self, model):
        self._model = model
        self.list_view.setModel(model)
        self.c = EmailListController(self.category, model)
        self._model.modelReset.connect(self.update_indexes)
        self.page_index.set_indexes(*model.current_index())


class ContactListController(PageListController):

    def __init__(self, category, model):
        super().__init__(model)

        self.category = category


class ContactListView(PageListView):

    def __init__(self, category, actions, parent=None):
        super().__init__(actions, parent=parent)

        self.category = category
        self.list_view.clicked.connect(self.emit_contact)

    def set_model(self, model):
        self._model = model
        self.list_view.setModel(model)
        self.c = ContactListController(self.category, model)
        self._model.modelReset.connect(self.update_indexes)
        self.page_index.set_indexes(*model.current_index())

    def emit_contact(self, qindex):
        idx = qindex.row()
        self._model.emit_email(idx)


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
