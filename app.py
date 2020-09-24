from PyQt5.QtWidgets import QApplication
# You have to import this before you can create QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
# ----------------------------------------------------------

import sys
import multiprocessing
import logging


if __name__ == '__main__':
    app = QApplication(sys.argv)

    testing = False
    if not testing:
        from views.views import AppView
        a = AppView()
    else:
        from utils import IPCTestingApp
        multiprocessing.log_to_stderr()
        logger = multiprocessing.get_logger()
        logger.setLevel(logging.INFO)
        m = IPCTestingApp()
        m.show()

    app.exec_()
