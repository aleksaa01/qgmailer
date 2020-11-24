from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal

from qmodels.email import EmailModel
from views.lists import EmailListView


class TrashPageController(object):

    def __init__(self):
        pass


class TrashPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.c = TrashPageController()

        self.tramod = EmailModel('trash')

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_trash = QWidget()
        self.list_trash = EmailListView('trash', None, parent=self.tab_trash)
        self.list_trash.set_model(self.tramod)
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(self.list_trash)
        self.tab_trash.setLayout(tab_layout)

        self.tab_widget.addTab(self.tab_trash, 'Trash')
        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)