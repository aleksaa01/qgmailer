from PyQt5.QtWidgets import QApplication

import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView


# TODO: Fix layout of Options page.
# TODO: Notify user if message was sent successfully or not.
# FIXME: Find the solution to single-releasable-shared-resource problem/bug.

if __name__ == '__main__':
    app = QApplication(sys.argv)
    from views.views import AppView
    a = AppView()
    app.exec_()
