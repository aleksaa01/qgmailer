from PyQt5.QtWidgets import QWidget, QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, \
    QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from qmodels.options import options
from channels.event_channels import OptionEventChannel


class OptionsPageController(object):

    def __init__(self, model):
        self._model = model

    def emails_per_page_changed(self, new_value):
        self._model.emails_per_page = int(new_value)
        OptionEventChannel.publish('emails_per_page', page_length=int(new_value))

    def contacts_per_page_changed(self, new_value):
        self._model.contacts_per_page = int(new_value)
        OptionEventChannel.publish('contacts_per_page', page_length=int(new_value))

    def font_size_changed(self, new_value):
        self._model.font_size = int(new_value)
        OptionEventChannel.publish('font_size', font_size=int(new_value))

    def theme_changed(self, new_value):
        self._model.theme = new_value
        OptionEventChannel.publish('theme', theme=new_value)

    def shortcut_changed(self, shortcut, new_value):
        setattr(self._model, shortcut, new_value)
        OptionEventChannel.publish(shortcut, **{shortcut: new_value})


# TODO: Maybe add shortcut edits to options, that doesn't seem like a bad idea.
#   It will populate a really emtpy area and make it look nicer and richer(still empty though :D)
#   Maybe I can put it inside of a distinguishable structure, like a group box.
#   Also If I do that, I will have to add FlowLayout because those 2 group boxes will have
#   to be placed vertically if window is too narrow.

# FIXME: Disallow users to have 2 same shortcuts, because that will make those 2
#   shortcuts emit activatedAmbiguously signal instead of activated.
class OptionsPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = options
        self.c = OptionsPageController(self.model)

        self.mlayout = QHBoxLayout()
        self.mlayout.setSpacing(25)
        self.mlayout.setAlignment(Qt.AlignCenter)

        label_layout = QVBoxLayout()
        options_layout = QVBoxLayout()
        label_layout.setSpacing(12)
        options_layout.setSpacing(12)

        emails_lbl = QLabel('Emails per page')
        label_layout.addWidget(emails_lbl)
        self.emails_cb = QComboBox()
        self.emails_cb.addItems([str(opt) for opt in self.model.all_emails_per_page])
        self.emails_cb.setCurrentIndex(self.model.all_emails_per_page.index(self.model.emails_per_page))
        self.emails_cb.currentTextChanged.connect(self.c.emails_per_page_changed)
        options_layout.addWidget(self.emails_cb)

        contacts_lbl = QLabel('Contacts per page')
        label_layout.addWidget(contacts_lbl)
        self.contacts_cb = QComboBox()
        self.contacts_cb.addItems([str(opt) for opt in self.model.all_contacts_per_page])
        self.contacts_cb.setCurrentIndex(self.model.all_contacts_per_page.index(self.model.contacts_per_page))
        self.contacts_cb.currentTextChanged.connect(self.c.contacts_per_page_changed)
        options_layout.addWidget(self.contacts_cb)

        font_size_lbl = QLabel('Font size')
        label_layout.addWidget(font_size_lbl)
        self.font_size_le = QLineEdit(str(self.model.font_size))
        self.font_size_le.editingFinished.connect(lambda: self.c.font_size_changed(self.font_size_le.text()))
        options_layout.addWidget(self.font_size_le)

        theme_lbl = QLabel('Theme')
        label_layout.addWidget(theme_lbl)
        self.theme_cb = QComboBox()
        self.theme_cb.addItems(self.model.all_theme)
        self.theme_cb.setCurrentIndex(self.model.all_theme.index(self.model.theme))
        self.theme_cb.currentTextChanged.connect(self.c.theme_changed)
        options_layout.addWidget(self.theme_cb)

        self.inbox_shortcut = self.add_shortcut_edit_option(
            'Inbox shortcut', options.inbox_shortcut, label_layout, options_layout)
        self.send_email_shortcut = self.add_shortcut_edit_option(
            'Send-Email shortcut', options.send_email_shortcut, label_layout, options_layout)
        self.sent_shortcut = self.add_shortcut_edit_option(
            'Sent shortcut', options.sent_shortcut, label_layout, options_layout)
        self.contacts_shortcut = self.add_shortcut_edit_option(
            'Contacts shortcut', options.contacts_shortcut, label_layout, options_layout)
        self.trash_shortcut = self.add_shortcut_edit_option(
            'Trash shortcut', options.trash_shortcut, label_layout, options_layout)
        self.options_shortcut = self.add_shortcut_edit_option(
            'Options shortcut', options.options_shortcut, label_layout, options_layout)

        self.inbox_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('inbox_shortcut', 'Ctrl+' + self.inbox_shortcut.text()))
        self.send_email_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('send_email_shortcut', 'Ctrl+' + self.send_email_shortcut.text()))
        self.sent_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('sent_shortcut', 'Ctrl+' + self.sent_shortcut.text()))
        self.contacts_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('contacts_shortcut', 'Ctrl+' + self.contacts_shortcut.text()))
        self.trash_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('trash_shortcut', 'Ctrl+' + self.trash_shortcut.text()))
        self.options_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('options_shortcut', 'Ctrl+' + self.options_shortcut.text()))

        self.mlayout.addLayout(label_layout)
        self.mlayout.addLayout(options_layout)

        lay = QHBoxLayout()
        lay.addStretch(1)
        lay.addLayout(self.mlayout)
        lay.addStretch(1)
        lay.setAlignment(Qt.AlignHCenter)
        self.setLayout(lay)

    def add_shortcut_edit_option(self, label_text, option, label_layout, option_layout):
        shortcut_lbl = QLabel(label_text)
        label_layout.addWidget(shortcut_lbl)
        shortcut_opt_lbl = QLabel('Ctrl+')
        shortcut_opt_le = QLineEdit(option.split('+')[1])
        shortcut_opt_le.setInputMask('>A;')
        lay = QHBoxLayout()

        lay.addWidget(shortcut_opt_lbl)
        lay.addWidget(shortcut_opt_le)
        option_layout.addLayout(lay)

        return shortcut_opt_le