from PyQt5.QtNetwork import QTcpServer, QTcpSocket

import multiprocessing
import pickle
import time

from services._async_fetcher import entrypoint
from services._async_fetcher import MAX_READ_BUF
from services.event import APIEvent, IPC_SHUTDOWN


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

        self.worker_socket = None
        self.next_event_id = 0
        self.callback_map = {} # event id to (api_event, callback) map
        self.request_queue = []

        self._phase = 0
        self._size_of_request_size = None
        self._request_size = None

        self.last_read = time.perf_counter()
    
    def _handle_connection(self):
        self.worker_socket = self.local_server.nextPendingConnection()
        print("Current worker socket state:", self.worker_socket.state())
        self.worker_socket.channelReadyRead.connect(self._read)
        self.local_server.close()

    def _read(self, channel_idx):
        t = time.perf_counter()
        s = t - self.last_read
        print("Time passed after the last read: ", s)
        t = time.perf_counter()
        if self._phase == 0:
            print("Phase 0...")
            if self.worker_socket.bytesAvailable() < 1:
                return
            raw_data = self.worker_socket.read(1)
            size_of_request_size = ord(raw_data.decode('utf-8'))
            self._size_of_request_size = size_of_request_size
            self._phase = 1
            print(f"length of request length parsed(raw_data: {raw_data}, len_of_request_len: {size_of_request_size})...")

        if self._phase == 1:
            print("Phase 1...")
            if self.worker_socket.bytesAvailable() < self._size_of_request_size:
                return
            raw_data = b''
            while len(raw_data) < self._size_of_request_size:
                raw_data += self.worker_socket.read(self._size_of_request_size - len(raw_data))
            request_size = int(raw_data.decode('utf-8'))
            self._request_size = request_size
            self._phase = 2
            print(f"request length parsed(request_len: {request_size})...")

        if self._phase == 2:
            print("Phase 2...")
            if self.worker_socket.bytesAvailable() < self._request_size:
                return
            raw_data = []
            received_data = 0
            while received_data < self._request_size:
                data = self.worker_socket.read(min(MAX_READ_BUF, self._request_size - received_data))
                received_data += len(data)
                raw_data.append(data)
            self._phase = 0
            print("raw data parsed...")

        api_event = pickle.loads(b''.join(raw_data))
        print("Child process has sent us an APIEvent with id: ", api_event.event_id)
        request_event, callback = self.callback_map[api_event.event_id]

        api_event.category = request_event.category
        callback(api_event)
        tt = time.perf_counter()
        s = tt - t
        print(f"_read() took: {s} seconds to complete...")
        self.last_read = tt
        if self.worker_socket.bytesAvailable() > 0:
            self.worker_socket.channelReadyRead.emit(channel_idx)

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

    def shutdown(self):
        api_event = APIEvent(self._next_event_id(), value=IPC_SHUTDOWN)
        self._write(api_event, flush=True)

        while self.fetch_worker_proc.is_alive():
            time.sleep(0.05)

        self.worker_socket.close()
        self.local_server.close()
