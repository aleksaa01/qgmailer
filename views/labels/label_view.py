from googleapis.gmail.labels import Label, GMAIL_LABEL_SENT, GMAIL_LABEL_TRASH
from channels.event_channels import EmailEventChannel
from qmodels.email import EmailModel
from views.labels.email_label import EmailLabel, TrashEmailLabel, SentEmailLabel

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer

from logs.loggers import default_logger

LOG = default_logger()


# TODO: Make sure to display appropriate icons next to label names
class LabelView(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.displayed_email_label = None
        font = QFont(QApplication.font())
        font.setPixelSize(14)
        self.label_title = QLabel('')
        self.label_title.setFont(font)

        mlayout = QVBoxLayout()
        mlayout.setContentsMargins(0, 0, 0, 0)
        mlayout.addWidget(self.label_title)
        self.setLayout(mlayout)

        generic = EmailLabel()
        sent = SentEmailLabel()
        trash = TrashEmailLabel()
        self.email_label_map = {EmailLabel: generic, SentEmailLabel: sent, TrashEmailLabel: trash}
        # Any label id that is not in the special_label_map should use generic EmailLabel
        self.special_label_map = {GMAIL_LABEL_SENT: SentEmailLabel, GMAIL_LABEL_TRASH: TrashEmailLabel}
        self.labels = {}

        EmailEventChannel.subscribe('show_label', self.show_label)
        EmailEventChannel.subscribe('labels_sync', self.process_labels)

    def process_labels(self, labels, error=''):
        assert not error

        if 'all' in labels:
            for label_data in labels['all']:
                label_object = Label(*label_data)
                email_label_class = self.special_label_map.get(label_object.id) or EmailLabel
                email_model = EmailModel(label_object.id, self._call_func_after)
                self.labels[label_object.id] = (label_object, email_label_class, email_model)
        else:
            for label_data in labels['modified']:
                new_label_object = Label(*label_data)
                _, email_label_class, email_model = self.labels[new_label_object.id]
                self.labels[new_label_object.id] = (new_label_object, email_label_class, email_model)
            for label_data in labels['deleted']:
                self.labels.pop(label_data[0])
            for label_data in labels['added']:
                label_object = Label(*label_data)
                email_label_class = self.special_label_map.get(label_object.id) or EmailLabel
                email_model = EmailModel(label_object.id, self._call_func_after)
                self.labels[label_object.id] = (label_object, email_label_class, email_model)


    def show_label(self, label_id):
        fields = self.labels.get(label_id)
        if fields is None:
            return
        label, email_label_class, email_model = fields
        layout = self.layout()
        if self.displayed_email_label:
            item = layout.takeAt(layout.count() - 1)
            item.widget().hide()

        email_label = self.email_label_map[email_label_class]
        email_label.set_model(label, email_model)
        self.displayed_email_label = email_label
        layout.addWidget(email_label)
        email_label.show()

        label_name = label.name
        if label_name.startswith('CATEGORY'):
            label_name = label_name.split('_')[1]
        label_name.capitalize()
        self.label_title.setText(f'<b>{label_name}</b>')
        # TODO: Check if this is needed.
        layout.update()

    def _call_func_after(self, func, seconds):
        # QTimer.singleShort expects milliseconds
        QTimer.singleShot(seconds * 1000, func)