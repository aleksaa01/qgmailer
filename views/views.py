from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QPixmap, QIcon


class AppView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('QGmailer')
        icon = QIcon(QPixmap(':/images/qgmailer_logo.png'))
        self.setWindowIcon(icon)
        self.setFixedSize(640, 480)
        self.show()



from views.icons import icons_rc