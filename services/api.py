from PyQt5.QtNetwork import QTcpServer

import multiprocessing
import pickle
import time

from services._async_fetcher import entrypoint
from services._async_fetcher import MAX_READ_BUF
from services.event import APIEvent, IPC_SHUTDOWN, NOTIFICATION_ID
from channels.event_channels import ProcessEventChannel
from logs.loggers import default_logger

LOG = default_logger()

DEFAULT_LOCAL_PORT = 10100


class APIService(object):

    def __init__(self):
        self.local_server = QTcpServer()
        self.local_server.newConnection.connect(self._handle_connection)
        increment = 0
        while (available := self.local_server.listen(port=DEFAULT_LOCAL_PORT + increment)) is False:
            increment += 1

        self.fetch_worker_proc = multiprocessing.Process(target=entrypoint, args=(DEFAULT_LOCAL_PORT + increment,))
        self.fetch_worker_proc.start()

        self.worker_socket = None
        self.next_event_id = 0
        # event id to (api_event, callback) map
        self.callback_map = {}
        # Used for queueing up requests that had been sent before the connection with the
        # other process was established
        self.request_queue = []

        self._phase = 0
        self._size_of_request_size = None
        self._request_size = None
    
    def _handle_connection(self):
        self.worker_socket = self.local_server.nextPendingConnection()
        self.worker_socket.channelReadyRead.connect(self._read)
        self.local_server.close()

        for data in self.request_queue:
            self._write(data)

    def _read(self, channel_idx):
        if self._phase == 0:
            if self.worker_socket.bytesAvailable() < 1:
                return
            raw_data = self.worker_socket.read(1)
            size_of_request_size = ord(raw_data.decode('utf-8'))
            self._size_of_request_size = size_of_request_size
            self._phase = 1

        if self._phase == 1:
            if self.worker_socket.bytesAvailable() < self._size_of_request_size:
                return
            raw_data = b''
            while len(raw_data) < self._size_of_request_size:
                raw_data += self.worker_socket.read(self._size_of_request_size - len(raw_data))
            request_size = int(raw_data.decode('utf-8'))
            self._request_size = request_size
            self._phase = 2

        if self._phase == 2:
            if self.worker_socket.bytesAvailable() < self._request_size:
                return
            raw_data = []
            received_data = 0
            while received_data < self._request_size:
                data = self.worker_socket.read(min(MAX_READ_BUF, self._request_size - received_data))
                received_data += len(data)
                raw_data.append(data)
            self._phase = 0

        api_event = pickle.loads(b''.join(raw_data))
        if api_event.event_id == NOTIFICATION_ID:
            event_channel = api_event.event_channel
            event_channel.publish(api_event.topic, **api_event.payload)
        else:
            callback = self.callback_map[api_event.event_id]
            callback(api_event)

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

        # Data won't be written to a socket immediately.
        # It will be written once you give back control to QEventLoop.
        # Unless you call flush() on the socket.
        total_sent_bytes = self.worker_socket.write(raw_data)
        if flush:
            self.worker_socket.flush()

    def _next_event_id(self):
        event_id = self.next_event_id
        self.next_event_id += 1
        return event_id

    def fetch(self, event_channel, topic, callback, **payload):
        api_event_id = self._next_event_id()
        api_event = APIEvent(api_event_id, event_channel, topic, **payload)
        self.callback_map[api_event_id] = callback

        if self.worker_socket is None:
            self.request_queue.append(api_event)
            return

        self._write(api_event)

    def shutdown(self):
        api_event = APIEvent(self._next_event_id(), event_channel=ProcessEventChannel,
                             topic='commands', flag=IPC_SHUTDOWN)
        self._write(api_event, flush=True)

        tries = 0
        while self.fetch_worker_proc.is_alive() and tries < 100:
            tries += 1
            time.sleep(0.05)

        if tries >= 100:
            # Terminate the worker process if it takes more than 5 seconds to shutdown. Otherwise a call
            # to join will block forever.
            self.fetch_worker_proc.terminate()

        # Even though call to .is_alive() will join the process, it's still good practice to join it
        # explicitly.
        self.fetch_worker_proc.join()

        self.worker_socket.close()
        self.local_server.close()
