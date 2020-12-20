from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QIcon, QPixmap


class ContactContext(object):
    def __init__(self):
        self._on_removed = lambda: None
        self.qmenu = QMenu()
        icon = QIcon(QPixmap(':/images/remove_icon.png'))
        self.qmenu.addAction(icon, 'Remove', self._on_removed)

    def on_removed(self, callback):
        self._on_removed = callback

    def show(self, position):
        self.qmenu.exec_(position)
