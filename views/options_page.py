from PyQt5.QtWidgets import QWidget, QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

from qmodels.options import options
from channels.event_channels import OptionEventChannel


class OptionsPageController(object):

    def __init__(self, model):
        self._model = model

    def emails_per_page_changed(self, new_value):
        self._model.emails_per_page = int(new_value)
        OptionEventChannel.publish('emails_per_page', {'value': int(new_value)})

    def contacts_per_page_changed(self, new_value):
        self._model.contacts_per_page = int(new_value)
        OptionEventChannel.publish('contacts_per_page', {'value': int(new_value)})

    def font_size_changed(self, new_value):
        self._model.font_size = new_value
        OptionEventChannel.publish('font_size', {'value': new_value})

    def theme_changed(self, new_value):
        self._model.theme = new_value
        OptionEventChannel.publish('theme', {'value': new_value})



class OptionsPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = options
        self.c = OptionsPageController(self.model)

        self.mlayout = QVBoxLayout()
        self.mlayout.setAlignment(Qt.AlignCenter)

        option_container = QWidget(self)
        emails_lbl = QLabel('Emails per page')
        self.emails_cb = QComboBox()
        self.emails_cb.addItems([str(opt) for opt in self.model.all_emails_per_page])
        self.emails_cb.setCurrentIndex(self.model.all_emails_per_page.index(self.model.emails_per_page))
        self.emails_cb.currentTextChanged.connect(self.c.emails_per_page_changed)
        layout = QHBoxLayout()
        layout.addWidget(emails_lbl)
        layout.addWidget(self.emails_cb)
        option_container.setLayout(layout)
        self.mlayout.addWidget(option_container)

        option_container = QWidget(self)
        contacts_lbl = QLabel('Contacts per page')
        self.contacts_cb = QComboBox()
        self.contacts_cb.addItems([str(opt) for opt in self.model.all_contacts_per_page])
        self.contacts_cb.setCurrentIndex(self.model.all_contacts_per_page.index(self.model.contacts_per_page))
        self.contacts_cb.currentTextChanged.connect(self.c.contacts_per_page_changed)
        layout = QHBoxLayout()
        layout.addWidget(contacts_lbl)
        layout.addWidget(self.contacts_cb)
        option_container.setLayout(layout)
        self.mlayout.addWidget(option_container)

        option_container = QWidget(self)
        font_size_lbl = QLabel('Font size')
        self.font_size_le = QLineEdit(str(self.model.font_size))
        self.font_size_le.editingFinished.connect(lambda: self.c.font_size_changed(self.font_size_le.text()))
        layout = QHBoxLayout()
        layout.addWidget(font_size_lbl)
        layout.addWidget(self.font_size_le)
        option_container.setLayout(layout)
        self.mlayout.addWidget(option_container)

        option_container = QWidget(self)
        theme_lbl = QLabel('Theme')
        self.theme_cb = QComboBox()
        self.theme_cb.addItems(self.model.all_theme)
        self.theme_cb.setCurrentIndex(self.model.all_theme.index(self.model.theme))
        self.theme_cb.currentTextChanged.connect(self.c.theme_changed)
        layout = QHBoxLayout()
        layout.addWidget(theme_lbl)
        layout.addWidget(self.theme_cb)
        option_container.setLayout(layout)
        self.mlayout.addWidget(option_container)

        self.setLayout(self.mlayout)