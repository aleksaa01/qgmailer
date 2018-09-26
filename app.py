from PyQt5.QtWidgets import QApplication
import sys
from dispatcher import Dispatcher
from views.main_view import MainView


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dispatcher = Dispatcher()
    window = MainView(dispatcher)
    window.show()
    app.exec_()
