from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP
from threading import Thread
from .singleton import Singleton
from .service import ServiceManager, ServiceUser


class UserConnection(ServiceUser):
    def __init__(self, server, sock, addr):
        assert isinstance(server, TeamServer)
        assert isinstance(sock, socket)
        self._socket = sock
        self._local_address, self._local_port = addr
        self._server = server
        self.services.parent = server.services

    def _handle(self):
        self.services.user.connection = self
        self.services.user.storage = {}

    def handle(self):
        self._thread = Thread(self._handle)
        self._thread.daemon = True
        self._thread.start()


class TeamServer(Singleton, ServiceUser):
    def __init__(self, address='0.0.0.0', port=0):
        self._address = address
        self._port = port
        self._sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        self._connections = []

    def start(self):
        self._sock.bind((self._address, self._port))
        self._sock.listen(5)

        try:
            while True:
                sock, addr = self._sock.accept()
                connection = UserConnection(self, sock, addr)
                self._connections.append(connection)
                connection.handle()
        finally:
            self._sock.close()


