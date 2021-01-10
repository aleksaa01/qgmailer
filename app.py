from PyQt5.QtWidgets import QApplication
# You have to import this before you can create QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
# ----------------------------------------------------------

import sys
import multiprocessing
import logging

from views.app import AppView


if __name__ == '__main__':
    app = QApplication(sys.argv)

    TESTING = True
    if TESTING:
        multiprocessing.log_to_stderr(logging.INFO)

    app_view = AppView()
    app_view.show()

    app.exec_()
