from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QIcon, QPixmap

from channels.signal_channels import SignalChannel


class ContactContext(object):

    on_removed = SignalChannel()

    def __init__(self):
        self.qmenu = QMenu()
        icon = QIcon(QPixmap(':/images/remove_icon.png'))
        self.qmenu.addAction(icon, 'Remove', self.action_remove)

    def action_remove(self):
        self.on_removed.emit()

    def show(self, position):
        self.qmenu.exec_(position)
