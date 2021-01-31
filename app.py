if __name__ == '__main__':
    import multiprocessing
    # This is required if you want to package your app with PyInstaller.
    # This gets rid of the "multiple windows spawning" problem.
    # Do this before you import anything else, you will avoid some performance issues.
    multiprocessing.freeze_support()

    from PyQt5.QtWidgets import QApplication
    # You have to import this before you can create QApplication
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    # ----------------------------------------------------------

    import sys
    from logs.loggers import default_logger, clear_log_file

    from views.app import AppView

    app = QApplication(sys.argv)

    TESTING = False
    if TESTING:
        logger = default_logger(testing=True)
    else:
        logger = default_logger(testing=False)


    app_view = AppView()
    app_view.show()

    app.exec_()
