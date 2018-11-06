from PyQt5.QtWidgets import QApplication
import sys
from dispatcher import Dispatcher
from views.main_view import MainView
from options import Options


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(Options.extract_theme())
    dispatcher = Dispatcher()
    window = MainView(dispatcher)
    window.show()
    app.exec_()
