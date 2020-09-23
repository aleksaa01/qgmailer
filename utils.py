class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

class IPCTestingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(500, 500)

        port = 10100
        self.local_server = QTcpServer()
        self.local_server.newConnection.connect(self.handle_connection)
        assert self.local_server.listen(port=port)

        self.fetch_worker_proc = multiprocessing.Process(target=entrypoint, args=(port,))
        self.fetch_worker_proc.start()

        self.t1 = None
        self.worker_socket = None

    def handle_connection(self):
        self.worker_socket = self.local_server.nextPendingConnection()
        print("Current worker socket state:", self.worker_socket.state())
        self.worker_socket.channelReadyRead.connect(self.read)
        self.local_server.close()

    def read(self, channel_idx):
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

    def mousePressEvent(self, event):
        self.t1 = time.perf_counter()
        data = APIEvent(1, 'personal')
        self.write(data)
        event.accept()

    def write(self, data, flush=False):
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
        total_sent_bytes = self.worker_socket.write(raw_data)
        if flush:
            self.worker_socket.flush()

        print("Data sent! Total bytes sent out of total: {}/{}".format(total_sent_bytes, len(raw_data)))

    def closeEvent(self, event):
        self.hide()
        # self.timer.stop()

        shutdown_event = APIEvent(2, value=IPC_SHUTDOWN)
        self.write(shutdown_event, flush=True)

        # self.selector.unregister(self.worker_socket)
        # try:
        #     self.worker_socket.shutdown(socket.SHUT_RD)
        #     self.worker_socket.close()
        # except OSError:
        #     # socket already closed
        #     pass

        self.worker_socket.close()
        self.local_server.close()

        while self.fetch_worker_proc.is_alive():
            time.sleep(0.05)

        event.accept()
