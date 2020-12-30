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

        self.mlayout.addLayout(label_layout)
        self.mlayout.addLayout(options_layout)

        lay = QHBoxLayout()
        lay.addStretch(1)
        lay.addLayout(self.mlayout)
        lay.addStretch(1)
        lay.setAlignment(Qt.AlignHCenter)
        self.setLayout(lay)
