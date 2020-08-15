from PyQt5.QtWidgets import QApplication

import sys
# from PyQt5.QtWebEngineWidgets import QWebEngineView


from fetchers.messages import APIFetcher
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer


import time
import multiprocessing
import socket
import selectors
import pickle
import logging

from fetchers.messages import entrypoint
from fetchers.messages import MAX_READ_BUF
from utils import APIEvent


class W(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(500, 500)

        self.selector = selectors.DefaultSelector()

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Pick first awailable port
        port = 10100
        while True:
            try:
                server_socket.bind(('localhost', port))
            except OSError:
                print(f"Failed to bind to port: {port}")
                port += 1
            else:
                break

        server_socket.listen(5)

        self.fetch_worker_proc = multiprocessing.Process(target=entrypoint, args=(port,))
        self.fetch_worker_proc.start()

        self.worker_socket, address = server_socket.accept()
        self.worker_socket.setblocking(False)
        self.selector.register(self.worker_socket, selectors.EVENT_READ, self.read)

        data = APIEvent(1, 'test', 'ipc', 42)
        request_data = pickle.dumps(data)
        request_data_size = str(len(request_data))
        size_len = chr(len(request_data_size))
        raw_data = size_len.encode('utf-8') + request_data_size.encode('utf-8') + request_data

        print("Sending data...")
        total_sent_bytes = 0
        while total_sent_bytes < len(raw_data):
            total_sent_bytes += self.worker_socket.send(raw_data[total_sent_bytes:])
        print("Data sent! Total bytes send:", total_sent_bytes)

        self.timer = QTimer()
        self.timer.timeout.connect(self.loop)
        self.timer.start(50)

    def read(self, sock, mask):
        raw_data = sock.recv(1)
        if len(raw_data) == 0:
            print("Connection has been closed...shutting down the connection...")
            sock.close()
        len_of_request_len = ord(raw_data.decode('utf-8'))


        raw_data = b''
        while len(raw_data) < len_of_request_len:
            raw_data += sock.recv(len_of_request_len - len(raw_data))

        request_len = int(raw_data.decode('utf-8'))

        raw_data = []
        received_data = 0
        while received_data < request_len:
            data = sock.recv(min(MAX_READ_BUF, request_len - received_data))
            received_data += len(data)
            raw_data.append(data)

        response_data = pickle.loads(b''.join(raw_data))
        print("Child process has sent us some data:", response_data)
        print("event_id, type, category, value", response_data.event_id, response_data.type, response_data.category, response_data.value)

        self.timer.stop()
        self.selector.unregister(sock)
        sock.shutdown(socket.SHUT_RD)
        sock.close()

    def loop(self):
        print("In loop...")
        events = self.selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

    def closeEvent(self, event):
        self.hide()
        try:
            self.worker_socket.shutdown(socket.SHUT_RD)
            self.worker_socket.close()
        except OSError:
            # socket alrady closed
            pass
        event.accept()


if __name__ == '__main__':
    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)
    app = QApplication(sys.argv)
    # from views.views import AppView
    # a = AppView()

    m = W()
    m.show()
    app.exec_()
    print("THE END")
