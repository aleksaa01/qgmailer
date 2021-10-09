from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from googleapis.gmail.labels import Label, GMAIL_LABEL_SENT, SYSTEM_LABEL
from views.labels.email_label import EmailLabel


class SentPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        label_sent = Label(GMAIL_LABEL_SENT, GMAIL_LABEL_SENT, SYSTEM_LABEL)
        self.view_sent_emails = EmailLabel(label_sent, self)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_widget.addTab(self.view_sent_emails, 'Sent')
        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)
