from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from channels.event_channels import ShortcutEventChannel, OptionEventChannel
from qmodels.options import options


class Shortcuts(object):
    def __init__(self, parent):
        self.personal_shortcut = QShortcut(QKeySequence(options.personal_shortcut), parent)
        self.social_shortcut = QShortcut(QKeySequence(options.social_shortcut), parent)
        self.updates_shortcut = QShortcut(QKeySequence(options.updates_shortcut), parent)
        self.promotions_shortcut = QShortcut(QKeySequence(options.promotions_shortcut), parent)
        self.forums_shortcut = QShortcut(QKeySequence(options.forums_shortcut), parent)
        self.sent_shortcut = QShortcut(QKeySequence(options.sent_shortcut), parent)
        self.unread_shortcut = QShortcut(QKeySequence(options.unread_shortcut), parent)
        self.important_shortcut = QShortcut(QKeySequence(options.important_shortcut), parent)
        self.starred_shortcut = QShortcut(QKeySequence(options.starred_shortcut), parent)
        self.trash_shortcut = QShortcut(QKeySequence(options.trash_shortcut), parent)
        self.spam_shortcut = QShortcut(QKeySequence(options.spam_shortcut), parent)
        self.send_email_shortcut = QShortcut(QKeySequence(options.send_email_shortcut), parent)
        self.contacts_shortcut = QShortcut(QKeySequence(options.contacts_shortcut), parent)
        self.settings_shortcut = QShortcut(QKeySequence(options.settings_shortcut), parent)

        self.personal_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('personal'))
        self.social_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('social'))
        self.updates_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('updates'))
        self.promotions_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('promotions'))
        self.forums_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('forums'))
        self.sent_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('sent'))
        self.unread_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('unread'))
        self.important_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('important'))
        self.starred_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('starred'))
        self.trash_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('trash'))
        self.spam_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('spam'))
        self.send_email_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('send_email'))
        self.contacts_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('contacts'))
        self.settings_shortcut.activated.connect(lambda: ShortcutEventChannel.publish('settings'))

        OptionEventChannel.subscribe(
            'personal_shortcut', lambda shortcut: self.personal_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'social_shortcut', lambda shortcut: self.social_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'updates_shortcut', lambda shortcut: self.updates_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'promotions_shortcut', lambda shortcut: self.promotions_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'forums_shortcut', lambda shortcut: self.forums_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'sent_shortcut', lambda shortcut: self.sent_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'unread_shortcut', lambda shortcut: self.unread_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'important_shortcut', lambda shortcut: self.important_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'starred_shortcut', lambda shortcut: self.starred_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'trash_shortcut', lambda shortcut: self.trash_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'spam_shortcut', lambda shortcut: self.spam_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'send_email_shortcut', lambda shortcut: self.send_email_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'contacts_shortcut', lambda shortcut: self.contacts_shortcut.setKey(QKeySequence(shortcut)))
        OptionEventChannel.subscribe(
            'settings_shortcut', lambda shortcut: self.settings_shortcut.setKey(QKeySequence(shortcut)))
        
        
