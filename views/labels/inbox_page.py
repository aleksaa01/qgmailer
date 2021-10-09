from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout

from googleapis.gmail.labels import Label, GMAIL_LABEL_PERSONAL, GMAIL_LABEL_UPDATES, \
    GMAIL_LABEL_SOCIAL, GMAIL_LABEL_PROMOTIONS, SYSTEM_LABEL
from views.labels.email_label import EmailLabel


class InboxPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        label_personal = Label(GMAIL_LABEL_PERSONAL, GMAIL_LABEL_PERSONAL, SYSTEM_LABEL)
        self.view_personal = EmailLabel(label_personal, self)

        label_updates = Label(GMAIL_LABEL_UPDATES, GMAIL_LABEL_UPDATES, SYSTEM_LABEL)
        self.view_updates = EmailLabel(label_updates, self)

        label_social = Label(GMAIL_LABEL_SOCIAL, GMAIL_LABEL_SOCIAL, SYSTEM_LABEL)
        self.view_social = EmailLabel(label_social, self)

        label_promotions = Label(GMAIL_LABEL_PROMOTIONS, GMAIL_LABEL_PROMOTIONS, SYSTEM_LABEL)
        self.view_promotions = EmailLabel(label_promotions, self)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_widget.addTab(self.view_personal, 'Personal')
        self.tab_widget.addTab(self.view_updates, 'Updates')
        self.tab_widget.addTab(self.view_social, 'Social')
        self.tab_widget.addTab(self.view_promotions, 'Promotions')

        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)
