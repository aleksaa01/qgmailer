from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QIcon

from googleapis.gmail.label_ids import *
from views.lists.lists import EmailListView
from qmodels.email import EmailModel


class InboxPageController(object):

    def __init__(self):
        pass


class InboxPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.c = InboxPageController()

        self.permod = EmailModel(LABEL_ID_PERSONAL)
        self.updmod = EmailModel(LABEL_ID_UPDATES)
        self.socmod = EmailModel(LABEL_ID_SOCIAL)
        self.promod = EmailModel(LABEL_ID_PROMOTIONS)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_personal = QWidget()
        self.list_personal = EmailListView(LABEL_ID_PERSONAL, parent=self.tab_personal)
        self.list_personal.set_model(self.permod)
        layout = QVBoxLayout()
        layout.addWidget(self.list_personal)
        self.tab_personal.setLayout(layout)

        self.tab_updates = QWidget()
        self.list_updates = EmailListView(LABEL_ID_UPDATES, parent=self.tab_updates)
        self.list_updates.set_model(self.updmod)
        layout = QVBoxLayout()
        layout.addWidget(self.list_updates)
        self.tab_updates.setLayout(layout)

        self.tab_social = QWidget()
        self.list_social = EmailListView(LABEL_ID_SOCIAL, parent=self.tab_social)
        self.list_social.set_model(self.socmod)
        layout = QVBoxLayout()
        layout.addWidget(self.list_social)
        self.tab_social.setLayout(layout)

        self.tab_promotions = QWidget()
        self.list_promotions = EmailListView(LABEL_ID_PROMOTIONS, parent=self.tab_promotions)
        self.list_promotions.set_model(self.promod)
        layout = QVBoxLayout()
        layout.addWidget(self.list_promotions)
        self.tab_promotions.setLayout(layout)

        self.tab_widget.addTab(self.tab_personal, 'Personal')
        self.tab_widget.addTab(self.tab_updates, 'Updates')
        self.tab_widget.addTab(self.tab_social, 'Social')
        self.tab_widget.addTab(self.tab_promotions, 'Promotions')

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)
