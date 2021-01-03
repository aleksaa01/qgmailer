from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PyQt5.QtCore import QSize, pyqtProperty, QPropertyAnimation
from PyQt5.QtGui import QIcon, QPixmap

from channels.event_channels import SidebarEventChannel


# TODO: Fix layout of the sidebar
# TODO: Redesign sidebar to look less like a button. Make current page distinguishable.
class Sidebar(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        #self.setFrameStyle(QFrame.Box | QFrame.Sunken)

        self.inbox_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/inbox_icon.png'))
        self.inbox_btn.setIcon(icon)
        self.inbox_btn.setIconSize(QSize(30, 30))
        self.inbox_btn.setMinimumSize(QSize(40, 40))
        self.inbox_btn.setFlat(True)
        self.inbox_btn.clicked.connect(lambda: self.emit_event('inbox_page'))

        send_email_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/send_icon.png'))
        send_email_btn.setIcon(icon)
        send_email_btn.setIconSize(QSize(30, 30))
        send_email_btn.setMaximumSize(QSize(40, 40))
        send_email_btn.setFlat(True)
        send_email_btn.clicked.connect(lambda: self.emit_event('send_email_page'))

        contacts_page_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/contacts_icon2.png'))
        contacts_page_btn.setIcon(icon)
        contacts_page_btn.setIconSize(QSize(30, 30))
        contacts_page_btn.setMaximumSize(QSize(40, 40))
        contacts_page_btn.setFlat(True)
        contacts_page_btn.clicked.connect(lambda: self.emit_event('contacts_page'))

        trash_page_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/trash_icon.png'))
        trash_page_btn.setIcon(icon)
        trash_page_btn.setIconSize(QSize(30, 30))
        trash_page_btn.setMaximumSize(QSize(40, 40))
        trash_page_btn.setFlat(True)
        trash_page_btn.clicked.connect(lambda: self.emit_event('trash_page'))

        options_page_btn = SidebarButton()
        icon = QIcon(QPixmap(':/images/options_button.png'))
        options_page_btn.setIcon(icon)
        options_page_btn.setIconSize(QSize(30, 30))
        options_page_btn.setMaximumSize(QSize(40, 40))
        options_page_btn.setFlat(True)
        options_page_btn.clicked.connect(lambda: self.emit_event('options_page'))

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.inbox_btn)
        self.layout.addWidget(send_email_btn)
        self.layout.addWidget(contacts_page_btn)
        self.layout.addWidget(trash_page_btn)
        self.layout.addWidget(options_page_btn)
        self.layout.addStretch(1)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def emit_event(self, topic):
        SidebarEventChannel.publish(topic)


class SidebarButton(QPushButton):

class SidebarButton(QToolButton):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setCheckable(True)
        self._opacity = 0
        self.anim = QPropertyAnimation(self, b'opacity')
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(255)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        if value != 1:
            self.setStyleSheet(
                "SidebarButton{border: 0px; background-color: "
                "qlineargradient(spread:pad, x1:0.909198, "
                "y1:0.091, x2:0.201, y2:0.971364, stop:0 "
                "rgba(217, 217, 217, %s), stop:1 rgba(128, 128, 128, %s));"
                "}" % (value, value))

    opacity = pyqtProperty('int', get_opacity, set_opacity)

    def enterEvent(self, event):
        if self.isChecked() is False:
            self.anim.stop()
            self.anim.setStartValue(self.anim.currentValue())
            self.anim.setEndValue(255)
            self.anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isChecked() is False:
            self.anim.stop()
            self.anim.setStartValue(self.anim.currentValue())
            self.anim.setEndValue(0)
            self.anim.start()

        super().leaveEvent(event)

    def set_checked(self, checked):
        self.setChecked(checked)
        self.anim.stop()
        self.anim.setStartValue(self.anim.currentValue())
        if checked:
            self.anim.setEndValue(255)
        else:
            self.anim.setEndValue(0)
        self.anim.start()