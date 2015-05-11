__author__ = 'Eric Johnson'
from ..framework.application import Application
import sys
import struct


class Client:
    def __init__(self, conn):
        self._conn = conn

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

    def start(self):
        while True:
            try:
                msg = self.recv_message()
            except OSError:
                break

            if msg[0] == 0:
                sys.stdout.write(msg[1:].decode('utf-8'))

            elif msg[0] == 1:
                self.send_message(input(msg[1:].decode('utf-8')).encode('utf-8'))

            elif msg[0] == 2:
                break


class ConsoleApplication(Application):
    @staticmethod
    def help(parser):
        """
        Launch an instance of the astra console.
        """
        parser.add_argument('host', help='Host to connect to in the form [hostname|ip]:[port]',
                            default='127.0.0.1:1337')

    def run(self):
        self.services.load()
        address, port = self.host.split(':')
        sock = self.services.socket()
        sock.connect((address, int(port)))

        Client(sock).start()
