from PyQt5.QtWidgets import QApplication

import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView


from fetchers.messages import APIFetcher
from multiprocessing import Queue
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer
import time


class APIEvent(object):
    def __init__(self, event_id, type, category='', value=0):
        self.event_id = event_id
        self.type = type
        self.category = category
        self.value = value


class W(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(500, 500)
        self.input_queue = Queue()
        self.output_queue = Queue()
        t1 = time.perf_counter()
        self.show()
        t2 = time.perf_counter()
        print("show() time >>>", t2 - t1)
        self.a = APIFetcher(self.input_queue, self.output_queue)
        before_start = time.time()
        self.a.start()
        t2 = time.perf_counter()
        print("Create and start APIFetcher >>>", t2 - t1)
        t2 = time.perf_counter()
        self.input_queue.put(APIEvent(1, 'gmail', 'personal', before_start))
        self.input_queue.put(APIEvent(2, 'gmail', 'social', before_start))
        print("queue.put() and APIEvent object creation time >>>", t2 - t1)
        self.running = True
        QTimer.singleShot(10, self.loop)

    def loop(self):
        while self.running:
            if self.output_queue.empty():
                QApplication.processEvents()
                continue
            event_id, data = self.output_queue.get(block=False)
            print("APIResponseEvent: {}...".format(event_id))
            print("Length of Data: {}".format(len(data)))
        print("NO LONGER RUNNING...")

    def closeEvent(self, event):
        self.hide()
        self.running = False
        self.input_queue.put(APIEvent(3, None))
        while self.a.is_alive():
            pass
        print("Is process alive: {}\nExitcode: {}".format(self.a.is_alive(), self.a.exitcode))
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # from views.views import AppView
    # a = AppView()

    m = W()
    app.exec_()
    print("THE END")
