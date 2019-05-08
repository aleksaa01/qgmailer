from PyQt5.QtCore import pyqtSignal, QThread


class ContactsFetcher(QThread):
    pageLoaded = pyqtSignal(list)
    threadFinished = pyqtSignal(str) # page token
