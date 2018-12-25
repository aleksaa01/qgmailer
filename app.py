from PySide2.QtWidgets import QApplication

import sys
import platform

from dispatcher import Dispatcher
from views.main_view import MainView
from options import Options
from PySide2.QtGui import QFont


SYSTEM_OS = platform.system()


def change_appearance(app):
    # change theme at the end so that changes can take effect.
    change_default_font(app)
    app.setStyleSheet(Options.extract_theme())


def change_default_font(app):
    # avoid weird characters in Linux by setting "DejaVu Sans"
    # as a default font and restricting font merging.
    if SYSTEM_OS == 'Windows':
        default_font = QFont()
        default_font.setPixelSize(Options.app_options['font_size'])
        app.setFont(default_font)
    elif SYSTEM_OS == 'Linux':
        default_font = QFont('DejaVu Sans')
        default_font.setPixelSize(Options.app_options['font_size'])
        QFont.setStyleStrategy(default_font, QFont.NoFontMerging)
        app.setFont(default_font)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    change_default_font(app)
    app.setStyleSheet(Options.extract_theme())

    Options.optionsChanged.connect(lambda: change_appearance(app))

    dispatcher = Dispatcher()
    window = MainView(dispatcher)
    window.show()
    app.exec_()
