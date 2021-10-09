from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from googleapis.gmail.labels import Label, GMAIL_LABEL_TRASH, SYSTEM_LABEL
from views.labels.email_label import EmailLabel


class TrashPageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        label_trash = Label(GMAIL_LABEL_TRASH, GMAIL_LABEL_TRASH, SYSTEM_LABEL)
        self.view_trash = EmailLabel(label_trash, self)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)

        self.tab_widget.addTab(self.view_trash, 'Trash')
        mlayout = QVBoxLayout()
        mlayout.addWidget(self.tab_widget)
        self.setLayout(mlayout)
