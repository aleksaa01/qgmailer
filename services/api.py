from PyQt5.QtNetwork import QTcpServer, QTcpSocket

import multiprocessing
import pickle
import time

from services._async_fetcher import entrypoint
from services._async_fetcher import MAX_READ_BUF
from utils import APIEvent, IPC_SHUTDOWN


DEFAULT_LOCAL_PORT = 10100


class APIService(object):

    def __init__(self):
        self.local_server = QTcpServer()
        self.local_server.newConnection.connect(self._handle_connection)
        # TODO: In regular socket programming, ports can be unavailable.
        #  Check if it's the same for QT.
        assert self.local_server.listen(port=DEFAULT_LOCAL_PORT)

        self.fetch_worker_proc = multiprocessing.Process(target=entrypoint, args=(DEFAULT_LOCAL_PORT,))
        self.fetch_worker_proc.start()

        self.t1 = None
        self.worker_socket = None
        self.next_event_id = 0
        self.callback_map = {} # event id to callback map
    
    def _handle_connection(self):
        self.worker_socket = self.local_server.nextPendingConnection()
        print("Current worker socket state:", self.worker_socket.state())
        self.worker_socket.channelReadyRead.connect(self._read)
        self.local_server.close()

    def _read(self, channel_idx):
        print("In handle read...")
        raw_data = self.worker_socket.read(1)
        if len(raw_data) == 0:
            print("Connection has been closed...")
            self.worker_socket.close()
        len_of_request_len = ord(raw_data.decode('utf-8'))

        raw_data = b''
        while len(raw_data) < len_of_request_len:
            raw_data += self.worker_socket.read(len_of_request_len - len(raw_data))
        request_len = int(raw_data.decode('utf-8'))

        raw_data = []
        received_data = 0
        while received_data < request_len:
            data = self.worker_socket.read(min(MAX_READ_BUF, request_len - received_data))
            received_data += len(data)
            raw_data.append(data)

        response_data = pickle.loads(b''.join(raw_data))
        t2 = time.perf_counter()
        print("TIME LAPSE: ", t2 - self.t1, '\n', t2, self.t1)
        print("Child process has sent us an APIEvent with id: ", response_data.event_id)

    def _write(self, data, flush=False):
        """
        :param data: Data to be written to worker socket.
        :param flush: Set to True when you know you are not going to give control back to QEventLoop.
        """
        request_data = pickle.dumps(data)
        request_data_size = str(len(request_data))
        size_len = chr(len(request_data_size))
        raw_data = size_len.encode('utf-8') + request_data_size.encode('utf-8') + request_data

        print("Sending data...")
        # Data won't be written to a socket immediately.
        # It will be written once you give back control to QEventLoop.
        total_sent_bytes = self.worker_socket._write(raw_data)
        if flush:
            self.worker_socket.flush()

        print("Data sent! Total bytes sent out of total: {}/{}".format(total_sent_bytes, len(raw_data)))

    def _next_event_id(self):
        event_id = self.next_event_id
        self.next_event_id += 1
        return event_id

    def fetch(self, category, callback):
        api_event_id = self._next_event_id()
        self.callback_map[api_event_id] = callback

        api_event = APIEvent(api_event_id, category)
        self._write(api_event)