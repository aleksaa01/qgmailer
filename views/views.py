from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog
from PyQt5.QtGui import QPixmap, QIcon


class AppView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('QGmailer')
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        self.setFixedSize(640, 480)
        self.show()


class InboxPage(QWidget):
    """ All pages inherit from Page base class."""
    def __init__(self):
        pass


class ContactsPage(QWidget):
    def __init__(self):
        pass


class SentPage(QWidget):
    def __init__(self):
        pass


class SendEmailPage(QWidget):
    def __init__(self):
        pass


class TrashPage(QWidget):
    def __init__(self):
        pass


class OptionsDialog(QDialog):
    def __init__(self):
        pass


class SidebarNavigation(QWidget):
    """
    :param switcher: Some sort of object or widget that can switch between the pages.
    Like QStackedWidget for example, or it can be some custom widget with predefined interface.
    :param pages: List of all pages(InboxPage, SendEmailPage, TrashPage)

    Think about how would you implement this. Because you can have a page itself contain
    an icon for representation(Like navigation_icon, as attribute of the class).
    And you could make it so positions of icons get displayed dynamically and not in particular order.
    """
    def __init__(self, switcher, pages):
        pass


from views.icons import icons_rc