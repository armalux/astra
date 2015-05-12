__author__ = 'Eric Johnson'
from ..service import ServiceUser
from ..proc import Callback
from ...commands import Console
import socket
import struct


class ClientHandler(ServiceUser):
    def __init__(self, server, conn, address, id):
        self._conn = conn
        self.id = id
        self._server = server
        self.remote_address, self.remote_port = address
        self._thread = Callback(self._handle).spawn(start=False, stop=conn.close)
        self.console = Console(self)

    def start(self):
        self._thread.start()

    def stop(self):
        self._thread.stop()

    def read(self, length):
        buffer = b''
        while len(buffer) < length:
            data = self._conn.recv(length - len(buffer))

            if data == b'':
                break

            buffer += data

        if len(buffer) != length:
            raise BrokenPipeError()

        return buffer

    def send_message(self, data):
        self._conn.send(struct.pack('<H', len(data)))
        self._conn.sendall(data)

    def recv_message(self):
        length = struct.unpack('<H', self.read(2))[0]
        data = self.read(length)
        return data

    def _handle(self):
        print('connection open')

        try:
            while True:
                line = self.console.prompt(self.console.red('astra') + ' > ')
                self.console.run(line)
                if line.strip() == 'exit':
                    self.send_message(b'\x02')
                    break

        except OSError:
            pass

        finally:
            try:
                self._conn.shutdown(socket.SHUT_RDWR)
                self._conn.close()
            except OSError:
                pass

            del self._server.clients[self.id]

        print('connection closed')


class TeamServer(ServiceUser):
    def __init__(self, address='0.0.0.0', port=65322, motd='Welcome to Astra Team Server', handler_class=None):
        if handler_class is None:
            self._handler_class = ClientHandler
        self._motd = motd
        self._socket = self.services.socket()
        self._thread = Callback(self._run, address, port).spawn(start=False, stop=self._socket.close)
        self._next_client_id = iter(range(0, 2**64))
        self.clients = {}

    @property
    def next_client_id(self):
        return next(self._next_client_id)

    def start(self):
        self._thread.start()

    def stop(self):
        self._thread.stop()
        for client in list(self.clients.values()):
            client.stop()

    def _run(self, address, port):
        self._socket.bind((address, int(port)))
        self._socket.listen(5)

        while True:
            try:
                conn, address = self._socket.accept()
            except ConnectionAbortedError as e:
                return

            client = ClientHandler(self, conn, address, self.next_client_id)
            self.clients[client.id] = client
            client.start()
