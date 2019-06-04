from PyQt5.QtWidgets import QApplication

import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from views.views import AppView
    a = AppView()
    app.exec_()
