__author__ = 'Eric Johnson'
from astra.framework.service import ServiceUser
from astra.framework.proc import Callback
from astra.framework.console import Console
import socket
import struct
import atexit


class ClientHandler(ServiceUser):
    def __init__(self, server, conn, address, id):
        self._conn = conn
        self.id = id
        self._server = server
        self.remote_address, self.remote_port = address
        self._thread = Callback(self._handle).spawn(start=False, stop=conn.close)
        self.console = Console(self)
        self._closed = False

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
        self.services.session.connection = self
        self.services.session.console = self.console
        self.services.session.server = self._server

        self.console.print('\n' + self._server.motd + '\n')
        try:
            while True:
                line = self.console.prompt(self.console.cyan('astra') + ' > ')
                if line.strip() == 'exit':
                    self.send_message(b'\x02')
                    break

                try:
                    self.console.run(line)

                except Exception as e:
                    self.console.print_traceback(e)

        except OSError:
            pass

        finally:
            try:
                self._conn.shutdown(socket.SHUT_RDWR)
                self._conn.close()
            except OSError:
                pass

            del self._server.clients[self.id]


class TeamServer(ServiceUser):
    def __init__(self, address='127.0.0.1', port=65322, motd='Welcome to Astra Team Server', handler_class=None):
        if handler_class is None:
            self._handler_class = ClientHandler
        self.motd = motd
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
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((address, int(port)))
        self._socket.listen(5)

        atexit.register(self._socket.close)

        while True:
            try:
                conn, address = self._socket.accept()
            except ConnectionAbortedError:
                return

            client = ClientHandler(self, conn, address, self.next_client_id)
            self.clients[client.id] = client
            client.start()
