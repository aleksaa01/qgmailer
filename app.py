from PyQt5.QtWidgets import QApplication
import sys
from dispatcher import Dispatcher
from views.main_view import MainView
from options import Options
from PyQt5.QtGui import QFontDatabase

def change_app_stylesheet(app):
    app.setStyleSheet(Options.extract_theme())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(Options.extract_theme())
    QFontDatabase.addApplicationFont(':/fonts/NotoSans/NotoSans-Regular.ttf')
    Options.optionsChanged.connect(lambda: change_app_stylesheet(app))
    dispatcher = Dispatcher()
    window = MainView(dispatcher)
    window.show()
    app.exec_()
