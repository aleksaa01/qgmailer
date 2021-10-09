from PyQt5.QtWidgets import QWidget, QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, \
    QFrame, QGroupBox
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
        OptionEventChannel.publish(shortcut, shortcut=new_value)


# FIXME: Disallow users to have 2 same shortcuts, because that will make those 2
#   shortcuts emit activatedAmbiguously signal instead of activated.
#   Solution to this is to inherit from QValidator and implement validate method.
#   Although I think this is too much hassle for little value, and even if user has
#   2 same shortcuts, he can figure out the problem because both of those 2 shortcuts
#   won't work.
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

        label_layout2 = QVBoxLayout()
        options_layout2 = QVBoxLayout()
        label_layout2.setSpacing(12)
        options_layout2.setSpacing(12)

        self.personal_shortcut = self.add_shortcut_edit_option(
            'Personal shortcut', options.personal_shortcut, label_layout2, options_layout2)
        self.social_shortcut = self.add_shortcut_edit_option(
            'Social shortcut', options.social_shortcut, label_layout2, options_layout2)
        self.updates_shortcut = self.add_shortcut_edit_option(
            'Updates shortcut', options.updates_shortcut, label_layout2, options_layout2)
        self.promotions_shortcut = self.add_shortcut_edit_option(
            'Promotions shortcut', options.promotions_shortcut, label_layout2, options_layout2)
        self.forums_shortcut = self.add_shortcut_edit_option(
            'Forums shortcut', options.forums_shortcut, label_layout2, options_layout2)
        self.sent_shortcut = self.add_shortcut_edit_option(
            'Sent shortcut', options.sent_shortcut, label_layout2, options_layout2)
        self.unread_shortcut = self.add_shortcut_edit_option(
            'Unread shortcut', options.unread_shortcut, label_layout2, options_layout2)
        self.important_shortcut = self.add_shortcut_edit_option(
            'Important shortcut', options.important_shortcut, label_layout2, options_layout2)
        self.starred_shortcut = self.add_shortcut_edit_option(
            'Starred shortcut', options.starred_shortcut, label_layout2, options_layout2)
        self.trash_shortcut = self.add_shortcut_edit_option(
            'Trash shortcut', options.trash_shortcut, label_layout2, options_layout2)
        self.spam_shortcut = self.add_shortcut_edit_option(
            'Spam shortcut', options.spam_shortcut, label_layout2, options_layout2)
        self.send_email_shortcut = self.add_shortcut_edit_option(
            'Send Email shortcut', options.send_email_shortcut, label_layout2, options_layout2)
        self.contacts_shortcut = self.add_shortcut_edit_option(
            'Contacts shortcut', options.contacts_shortcut, label_layout2, options_layout2)
        self.settings_shortcut = self.add_shortcut_edit_option(
            'Settings shortcut', options.settings_shortcut, label_layout2, options_layout2)

        self.personal_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('personal_shortcut', 'Ctrl+' + self.personal_shortcut.text()))
        self.social_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('social_shortcut', 'Ctrl+' + self.social_shortcut.text()))
        self.updates_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('updates_shortcut', 'Ctrl+' + self.updates_shortcut.text()))
        self.promotions_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('promotions_shortcut', 'Ctrl+' + self.promotions_shortcut.text()))
        self.forums_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('forums_shortcut', 'Ctrl+' + self.forums_shortcut.text()))
        self.sent_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('sent_shortcut', 'Ctrl+' + self.sent_shortcut.text()))
        self.unread_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('unread_shortcut', 'Ctrl+' + self.unread_shortcut.text()))
        self.important_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('important_shortcut', 'Ctrl+' + self.important_shortcut.text()))
        self.starred_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('starred_shortcut', 'Ctrl+' + self.starred_shortcut.text()))
        self.trash_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('trash_shortcut', 'Ctrl+' + self.trash_shortcut.text()))
        self.spam_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('spam_shortcut', 'Ctrl+' + self.spam_shortcut.text()))
        self.send_email_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('send_email_shortcut', 'Ctrl+' + self.send_email_shortcut.text()))
        self.contacts_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('contacts_shortcut', 'Ctrl+' + self.contacts_shortcut.text()))
        self.settings_shortcut.editingFinished.connect(
            lambda: self.c.shortcut_changed('settings_shortcut', 'Ctrl+' + self.settings_shortcut.text()))


        g1 = QGroupBox("General")
        glay1 = QHBoxLayout()
        glay1.setSpacing(25)
        glay1.setAlignment(Qt.AlignVCenter)
        glay1.addLayout(label_layout)
        glay1.addLayout(options_layout)
        g1.setLayout(glay1)

        g2 = QGroupBox("Shortcuts")
        glay2 = QHBoxLayout()
        glay2.setSpacing(25)
        glay2.setAlignment(Qt.AlignCenter)
        glay2.addLayout(label_layout2)
        glay2.addLayout(options_layout2)
        glay2.addStretch(1)
        g2.setLayout(glay2)

        self.mlayout.addWidget(g1)
        self.mlayout.addWidget(g2)

        lay = QHBoxLayout()
        lay.addStretch(1)
        lay.addLayout(self.mlayout)
        lay.addStretch(1)
        lay.setAlignment(Qt.AlignHCenter)
        self.setLayout(lay)

    def add_shortcut_edit_option(self, label_text, option, label_layout, option_layout):
        shortcut_lbl = QLabel(label_text)
        label_layout.addWidget(shortcut_lbl)
        shortcut_opt_lbl = QLabel('Ctrl +')
        shortcut_opt_le = QLineEdit(option.split('+')[1])
        shortcut_opt_le.setInputMask('>A;')
        lay = QHBoxLayout()

        lay.addWidget(shortcut_opt_lbl)
        lay.addWidget(shortcut_opt_le)
        option_layout.addLayout(lay)

        return shortcut_opt_le