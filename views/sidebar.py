from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QToolButton
from PyQt5.QtCore import QSize, pyqtProperty, QPropertyAnimation, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap


class Sidebar(QFrame):

    on_select = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        inbox_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/inbox_icon.png'))
        inbox_btn.setIcon(icon)
        inbox_btn.setIconSize(QSize(30, 30))
        inbox_btn.setMinimumSize(QSize(45, 45))
        inbox_btn.clicked.connect(lambda: self.emit_event(0))

        send_email_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/send_icon.png'))
        send_email_btn.setIcon(icon)
        send_email_btn.setIconSize(QSize(30, 30))
        send_email_btn.setMinimumSize(QSize(45, 45))
        send_email_btn.clicked.connect(lambda: self.emit_event(1))

        sent_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/sent_icon.png'))
        sent_btn.setIcon(icon)
        sent_btn.setIconSize(QSize(30, 30))
        sent_btn.setMinimumSize(QSize(45, 45))
        sent_btn.clicked.connect(lambda: self.emit_event(2))

        contacts_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/contacts_icon2.png'))
        contacts_btn.setIcon(icon)
        contacts_btn.setIconSize(QSize(30, 30))
        contacts_btn.setMinimumSize(QSize(45, 45))
        contacts_btn.clicked.connect(lambda: self.emit_event(3))

        trash_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/trash_icon.png'))
        trash_btn.setIcon(icon)
        trash_btn.setIconSize(QSize(30, 30))
        trash_btn.setMinimumSize(QSize(45, 45))
        trash_btn.clicked.connect(lambda: self.emit_event(4))

        options_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/options_button.png'))
        options_btn.setIcon(icon)
        options_btn.setIconSize(QSize(30, 30))
        options_btn.setMinimumSize(QSize(45, 45))
        options_btn.clicked.connect(lambda: self.emit_event(5))

        self.current_button = None
        self.button_count = 6

        main_layout = QVBoxLayout()
        main_layout.addWidget(inbox_btn)
        main_layout.addWidget(send_email_btn)
        main_layout.addWidget(sent_btn)
        main_layout.addWidget(contacts_btn)
        main_layout.addWidget(trash_btn)
        main_layout.addWidget(options_btn)
        main_layout.addStretch(1)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def emit_event(self, idx):
        self.select(idx)
        self.on_select.emit(idx)

    def select(self, idx):
        button = self.find_idx(idx)
        if button is None:
            if self.current_button:
                self.current_button.set_checked(False)
            self.current_button = None
        else:
            if self.current_button:
                self.current_button.set_checked(False)
            self.current_button = button
            button.set_checked(True)
    
    def find_idx(self, idx):
        if idx >= self.button_count:
            return None
        cur_idx = -1
        for widget in self.children():
            if isinstance(widget, SidebarButton):
                cur_idx += 1
                if cur_idx == idx:
                    return widget

