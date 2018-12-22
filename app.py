from PyQt5.QtWidgets import QApplication

import sys
import platform

from dispatcher import Dispatcher
from views.main_view import MainView
from options import Options
from PyQt5.QtGui import QFont


def change_app_stylesheet(app):
    app.setStyleSheet(Options.extract_theme())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(Options.extract_theme())

    system_os = platform.system()
    # avoid weird characters in Linux by setting "DejaVu Sans"
    # as a default font and restricting font merging.
    if system_os == 'Linux':
        default_font = QFont('DejaVu Sans')
        QFont.setStyleStrategy(default_font, QFont.NoFontMerging)
        app.setFont(default_font)

    Options.optionsChanged.connect(lambda: change_app_stylesheet(app))
    dispatcher = Dispatcher()
    window = MainView(dispatcher)
    window.show()
    app.exec_()
