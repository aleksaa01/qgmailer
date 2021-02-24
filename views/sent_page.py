from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from qmodels.email import EmailModel
from views.lists.lists import EmailListView


class SentPageController(object):

    def __init__(self):
        pass


class SentPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.c = SentPageController()

        self.sentmod = EmailModel('sent')

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_sent = QWidget()
        self.list_sent = EmailListView('sent', parent=self.tab_sent)
        self.list_sent.set_model(self.sentmod)
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(self.list_sent)
        self.tab_sent.setLayout(tab_layout)

        self.tab_widget.addTab(self.tab_sent, 'Sent')
        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)
