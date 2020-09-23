from PyQt5.QtWidgets import QApplication

import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView


from fetchers.messages import APIFetcher
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtNetwork import QTcpServer, QTcpSocket


import time
import multiprocessing
import socket
import selectors
import pickle
import logging

from fetchers.messages import entrypoint
from fetchers.messages import MAX_READ_BUF
from utils import APIEvent, IPC_SHUTDOWN


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
