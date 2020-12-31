from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtCore import Qt

from channels.event_channels import SidebarEventChannel, OptionEventChannel
from qmodels.options import options


class Shortcuts(object):
    def __init__(self, parent):
        self.inbox_shortcut = QShortcut(QKeySequence(options.inbox_shortcut), parent)
        self.send_email_shortcut = QShortcut(QKeySequence(options.send_email_shortcut), parent)
        self.contacts_shortcut = QShortcut(QKeySequence(options.contacts_shortcut), parent)
        self.trash_shortcut = QShortcut(QKeySequence(options.trash_shortcut), parent)
        self.options_shortcut = QShortcut(QKeySequence(options.options_shortcut), parent)

        self.inbox_shortcut.activated.connect(lambda: SidebarEventChannel.publish('inbox_page'))
        self.send_email_shortcut.activated.connect(lambda: SidebarEventChannel.publish('send_email_page'))
        self.contacts_shortcut.activated.connect(lambda: SidebarEventChannel.publish('contacts_page'))
        self.trash_shortcut.activated.connect(lambda: SidebarEventChannel.publish('trash_page'))
        self.options_shortcut.activated.connect(lambda: SidebarEventChannel.publish('options_page'))

        OptionEventChannel.subscribe(
            'inbox_shortcut', lambda inbox_shortcut: self.inbox_shortcut.setKey(QKeySequence(inbox_shortcut))
        )
        OptionEventChannel.subscribe(
            'send_email_shortcut', lambda send_email_shortcut: self.send_email_shortcut.setKey(QKeySequence(send_email_shortcut))
        )
        OptionEventChannel.subscribe(
            'contacts_shortcut', lambda contacts_shortcut: self.contacts_shortcut.setKey(QKeySequence(contacts_shortcut))
        )
        OptionEventChannel.subscribe(
            'trash_shortcut', lambda trash_shortcut: self.trash_shortcut.setKey(QKeySequence(trash_shortcut))
        )
        OptionEventChannel.subscribe(
            'options_shortcut', lambda options_shortcut: self.options_shortcut.setKey(QKeySequence(options_shortcut))
        )
