import socket
import fcntl
import struct
from ..framework.service import SingletonServiceProvider


class SocketException(Exception):
    pass


class SocketService(socket.socket):
    __provider__ = SingletonServiceProvider('socket', SocketService)
    __promiscuous = False
    __raw = False

    def close(self):
        if self.__raw and self.promiscuous:
            self.promiscuous = False

        return super().close()

    @staticmethod
    def interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', bytes(ifname[:15],'ascii'))
        )[20:24])

    @classmethod
    def raw(cls, interface, protocol, promiscuous=True):
        s = cls(socket.AF_INET, socket.SOCK_RAW, protocol)

        # Bind to the specified interface.
        if interface:
            if re.match('^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$', interface):
                s.bind((interface, 0))
            else:
                s.bind((cls.interface_ip(interface), 0))

        # Enter promiscuous mode
        s.promiscuous = promiscuous

        # Enable sending of the IP header.
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

        s.__raw = True

        return s

    @classmethod
    def raw_ethernet(cls, interface, promiscuous=True):
        return cls.raw(interface, socket.ntohs(0x0003), promiscuous)

    @classmethod
    def raw_tcp(cls, interface, promiscuous=True):
        return cls.raw(interface, socket.IPPROTO_TCP, promiscuous)

    @classmethod
    def raw_udp(cls, interface, promiscuous=True):
        return cls.raw(interface, socket.IPPROTO_UDP, promiscuous)

    @classmethod
    def raw_icmp(cls, interface, promiscuous=True):
        return cls.raw(interface, socket.IPPROTO_ICMP, promiscuous)

    def raw_listen(self, callback):
        if not self.__raw:
            raise SocketException('Cannot perform raw listen on non-raw socket.')

        while True:
            callback(self.recvfrom(65565))

    @property
    def promiscuous(self):
        return self.__promiscuous

    @promiscuous.setter
    def promiscuous(self, value):
        assert isinstance(value, bool)
        if not self.__raw and value:
            raise SocketException('Cannot enter promiscuous mode for a non-raw socket.')

        if self.__promiscuous == value:
            return

        if value:
            self.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
        else:
            self.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)

        self._promiscuous = value


provider = SingletonServiceProvider(Socket)
