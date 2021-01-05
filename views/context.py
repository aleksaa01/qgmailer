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


class InboxEmailContext(object):

    on_trashed = SignalChannel()

    def __init__(self):
        self.qmenu = QMenu()
        icon = QIcon(QPixmap(':/images/trash_icon.png'))
        self.qmenu.addAction(icon, 'Move to Trash', self.action_trash)

    def action_trash(self):
        self.on_trashed.emit()

    def show(self, position):
        self.qmenu.exec_(position)


class TrashEmailContext(object):

    on_restored = SignalChannel()
    on_deleted = SignalChannel()

    def __init__(self):
        self.qmenu = QMenu()
        icon = QIcon(QPixmap(':/images/trash_restore.png'))
        self.qmenu.addAction(icon, 'Restore', self.action_restore)
        icon = QIcon(QPixmap(':/images/remove_icon.png'))
        self.qmenu.addAction(icon, 'Delete forever', self.action_delete)

    def action_restore(self):
        self.on_restored.emit()

    def action_delete(self):
        self.on_deleted.emit()

    def show(self, position):
        self.qmenu.exec_(position)
