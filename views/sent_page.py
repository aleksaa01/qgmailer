from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from googleapis.gmail.label_ids import LABEL_ID_SENT
from qmodels.email import EmailModel
from views.lists.lists import EmailListView


class SentPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.sentmod = EmailModel(LABEL_ID_SENT)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_sent = QWidget()
        self.list_sent = EmailListView(LABEL_ID_SENT, parent=self.tab_sent)
        self.list_sent.set_model(self.sentmod)
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(self.list_sent)
        self.tab_sent.setLayout(tab_layout)

        self.tab_widget.addTab(self.tab_sent, 'Sent')
        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)
