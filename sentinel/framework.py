import os
import string
import random
import math
import binascii
import socket
import re
import fcntl
import struct


class MungerException(Exception):
    pass


class SocketException(Exception):
    pass


class Socket(socket.socket):
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

class Munger:
    '''
    Will alter a byte string to make it unreadable, but easily reversible.
    Nothing here is "cryptographically secure", but helps fight automated
    intrusion/malware detection systems.
    '''
    def xor(self, data, key):
        '''
        XOR a bytearray or bytes object against a single byte key.
        '''
        assert isinstance(key, int)
        assert isinstance(data, (bytes, bytearray))

        if not len(data):
            raise MungerException('Data must not be zero length.')

        if key > 256 or key < 0:
            raise MungerException('Key must be 0-255')

        table = bytes([key ^ i for i in range(0,256)])

        return data.translate(table)

    def multi_byte_xor(self, data, key):
        '''
        XOR a bytearray or bytes object against a multi byte key.
        '''
        assert isinstance(data, (bytes, bytearray))
        assert isinstance(key, (bytes, bytearray))

        if not len(data):
            raise MungerException('Data must not be zero length.')

        if not len(key):
            raise MungerException('Key must not be zero length.')

        if isinstance(data, bytes):
            data = bytearray(data)

        k = 0
        for i in range(len(data)):
            data[i] = data[i] ^ key[k]
            k += 1
            if k == len(key):
                k = 0

        return bytes(data)

    def rolling_xor(self, data, key):
        '''
        Perform a rolling XOR in a bytes or bytearray object.
        '''
        assert isinstance(data, (bytes, bytearray))
        assert isinstance(key, int)

        if not len(data):
            raise MungerException('Data must not be zero length.')

        if key < 0 or key > 255:
            raise MungerException('Key must be 0-255.')

        if isinstance(data, bytes):
            data = bytearray(data)

        for i in range(len(data)):
            new_k = data[i]
            data[i] = data[i] ^ k
            k = new_k

        return bytes(data)

    def multi_byte_rolling_xor(self, data, key):
        assert isinstance(data, (bytes, bytearray))
        assert isinstance(key, (bytes, bytearray))

        if not len(data):
            raise MungerException('Data must not be zero length.')

        if not len(key):
            raise MungerException('Key must not be zero length.')

        if isinstance(data, bytes):
            data = bytearray(data)

        if isinstance(key, bytes):
            key = bytearray(key)

        k = 0
        for i in range(len(data)):
            new_k = data[i]
            data[i] = data[i] ^ key[k]
            key[k] = new_k
            k += 1
            if k == len(key):
                k = 0

        return data

    def rotating_xor(self, data, key, bits=3):
        '''
        XOR a bytearray or bytes object, performing a 8-bit bitwise right rotation by 'bits'.
        '''
        assert isinstance(data, (bytes, bytearray))
        assert isinstance(key, int)

        if not len(data):
            raise MungerException('Data must not be zero length.')

        if key < 0 or key > 255:
            raise MungerException('Key must be 0-255.')

        if isinstance(data, bytes):
            data = bytearray(data)

        for i in range(len(data)):
            data[i] = data[i] ^ key
            key = ((key >> bits) | (key << (8 - bits) & 0xFF))

        return data

    def multi_byte_rotating_xor(self, data, key, bits=3):
        '''
        XOR a bytearray or bytes objects with a multibyte key, while rotating each byte of the key.
        '''
        assert isinstance(data, (bytes, bytearray))
        assert isinstance(key, (bytes, bytearray))

        if not len(data):
            raise MungerException('Data must not be zero length.')

        if not len(key):
            raise MungerException('Key must not be zero length.')

        if isinstance(data, bytes):
            data = bytearray(data)

        if isinstance(key, bytes):
            key = bytearray(key)

        k = 0
        for i in range(len(data)):
            data[i] = data[i] ^ key[k]
            key[k] = ((key[k] >> bits) | (key[k] << (8 - bits) & 0xFF))
            k += 1
            if k == len(key):
                k = 0

        return data

    def munge(self, data):
        key = os.urandom(4)
        data = self.multi_byte_rotating_xor(data, key)
        return key + data

    def unmunge(self, data):
        return self.multi_byte_rotating_xor(data[4:], data[:4])


class Random:
    '''
    A set of relatively fast random data algorithms.
    '''
    __system_random = None

    @property
    def system_random(self):
        '''
        An instance of random.SystemRandom used by some operations, but not all, due to performance.
        '''
        if self.__system_random is None:
            self.__system_random = random.SystemRandom()
        return self.__system_random

    def bytes(self, length, avoid=b''):
        '''
        Gets secure random bytes, avoiding the bytes specified.
        '''
        ret = b''
        avoid = bytes(set(avoid))
        while len(ret) != length:
            data = os.urandom(length - len(ret)).translate(None, avoid)
            ret += data

        return ret

    def integer(self, *args):
        '''
        Generates a secure random integer
        integer() - min is 0, max is signed 32 bit max
        integer(max)
        integer(min, max)
        '''
        if len(args) == 0:
            minimum, maximum = 0, 2**32

        elif len(args) == 1:
            minimum, maximum = 0, args[0]

        elif len(args) == 2:
            minimum, maximum = args

        return self.system_random.randint(minimum, maximum)

    def sample(self, sequence, length, avoid=b''):
        '''
        Select a random sample of bytes from the given sequence of bytes, avoiding those specified.
        The sample size may be larger than the sequence, and the selections may repeat.
        '''
        assert isinstance(sequence, bytes) or isinstance(sequence, bytearray)
        sequence = bytearray(set(sequence))
        avoid = bytes(set(avoid))
        for a in avoid:
            if a in sequence:
                sequence.pop(sequence.find(a))
        return bytes([sequence[x % len(sequence)] for x in os.urandom(length)])

    def printable(self, length, avoid=b''):
        '''
        Gets ascii printable-range secure random bytes, avoiding bytes specified.
        '''
        return self.sample(bytes(range(32,127)), length, avoid)

    def alphabetic(self, length, avoid=b''):
        '''
        Gets mixed-case alphabetic ascii secure random bytes.
        '''
        return self.sample(bytes(range(65,91)) + bytes(range(97, 123)), length, avoid)

    def alphabetic_lower(self, length, avoid=b''):
        '''
        Gets lower-case alphabetic ascii secure random bytes.
        '''
        return self.sample(bytes(range(97,123)), length, avoid)

    def alphabetic_upper(self, length, avoid=b''):
        '''
        Gets upper-case alphabetic ascii secure random bytes.
        '''
        return self.sample(bytes(range(65,91)), length, avoid)

    def numeric(self, length, avoid=b''):
        '''
        Gets numeric ascii secure random bytes.
        '''
        return self.sample(bytes(range(48,58)), length, avoid)

    def alphanumeric(self, length, avoid=b''):
        '''
        Gets mixed-case alphanumeric ascii secure random bytes.
        '''
        return self.sample(bytes(range(48,58)) + bytes(range(65,91)) + bytes(range(97,123)), length, avoid)

    def alphanumeric_lower(self, length, avoid=b''):
        '''
        Gets lower-case alphanumeric ascii secure random bytes.
        '''
        return self.sample(bytes(range(48,58)) + bytes(range(97,123)), length, avoid)

    def alphanumeric_upper(self, length, avoid=b''):
        '''
        Gets upper-case alphanumeric ascii secure random bytes.
        '''
        return self.sample(bytes(range(48,58)) + bytes(range(65,91)), length, avoid)

    def hex(self, length, avoid=b'', decodable=True):
        '''
        Returns a bytes string of random (upper-case) ascii hexadecimal characters.
        If decodable=True, will return a hex string >= the specified length that can be decoded into bytes
        If decodable=False, will return a hex string, exactly the specified length, not guarenteed to decode.
        '''
        if decodable:
            if length < 2:
                length = 2
            if length % 2 != 0:
                length += 1

        return self.sample(bytes(range(48,58)) + bytes(range(65,71)), length, avoid)

    def base64(self, length, avoid=b'', decodable=True):
        '''
        Returns a bytes string of random ascii base-64 characters.
        If decodable=True, will create a decodable base64 string who's length is >= the specified length, may include avoid characters.
        If decodable=False, will create a bytes string of the exact length specified, but it may not decode.
        '''
        if not decodable:
            return self.sample(bytes(range(48,58)) + bytes(range(65,91)) + bytes(range(97,123)) + b'+/', length, avoid)

        return binascii.b2a_base64(self.bytes(math.ceil(float(length) * (5.0/6.0))))


class Callback:
    def __init__(self, function, *args, **kwargs):
        self.__function = function
        self.__args = args
        self.__kwargs = kwargs

    def run(self):
        return self.__function(*self.__args, **self.__kwargs)

    def call(self, *args, **kwargs):
        return self.__function(*args, **kwargs)

    def fork(self, *args, **kwargs):
        return Forker(self).fork(*args, **kwargs)

    def __mul__(self, number):
        assert isinstance(number, int)
        if number == 0:
            return []

        return [self for x in range(0, number)]


class Forker:
    def __init__(self, *callbacks):
        for callback in callbacks:
            assert isinstance(callback, Callback)

        self.__callbacks = callbacks

    def fork(self, daemonize=False, wait=True, exit_function=None):
        if exit_function is None:
            exit_function = exit

        pids = []
        for callback in self.__callbacks:
            pid = os.fork()
            if pid != 0:
                pids.append(pid)
                continue

            if daemonize:
                os.setsid()

            try:
                retval = callback.run()
                exit_function(retval)

            except Exception:
                exit(-1)

            finally:
                exit(0)

        if not daemonize and wait:
            for pid in pids:
                os.waitpid(pid, 0)

        return pids


class ServiceException(Exception):
    pass


class ServiceProvider:
    @property
    def name(self):
        raise NotImplementedError()

    @property
    def instance(self):
        raise NotImplementedError()


class ClassServiceProvider(ServiceProvider):
    __service_class = None
    __name = None

    def __init__(self, name, service_class):
        self.__service_class = service_class
        self.__name = name

    @property
    def name(self):
        return self.__name

    @property
    def instance(self):
        return self.__service_class


class SimpleServiceProvider(ServiceProvider):
    __service_class = None
    __name = None
    __args = None
    __kwargs = None

    def __init__(self, name, service_class, *args, **kwargs):
        assert isinstance(name, str)
        assert isinstance(service_class, type)

        self.__service_class = service_class
        self.__name = name
        self.__args = args
        self.__kwargs = kwargs

    @property
    def args(self):
        return self.__args

    @property
    def kwargs(self):
        return self.__kwargs

    @property
    def name(self):
        return self.__name

    @property
    def service_class(self):
        return self.__service_class


class SingletonServiceProvider(SimpleServiceProvider):
    __instance = None

    @property
    def instance(self):
        if self.__instance is None:
            self.__instance = self.service_class(*self.args, **self.kwargs)
        return self.__instance


class FactoryServiceProvider(SimpleServiceProvider):
    @property
    def instance(self):
        return self.service_class(*self.args, **self.kwargs)


class ServiceManager:
    def __init__(self):
        self.__providers = {}

    def __getitem__(self, key):
        if key not in self.__providers:
            raise ServiceException('No such service "{0}"'.format(key))
        return self.__providers[key].instance

    def __getattr__(self, key):
        if key == '__providers':
            return object.__getattribute__(self, '__providers')

        return self.__getitem__(key)

    def __setitem__(self, key, value):
        assert isinstance(value, ServiceProvider)
        if key in self.__providers:
            raise ServiceException('Service "{0}" already exists.'.format(key))
        self.__providers[key] = value

    def register(self, provider):
        assert isinstance(provider, ServiceProvider)
        self.__setitem__(provider.name, provider)

    @classmethod
    def default(cls):
        mgr = cls()
        mgr.register(SingletonServiceProvider('random', Random))
        mgr.register(SingletonServiceProvider('munger', Munger))
        mgr.register(ClassServiceProvider('socket', Socket))
        return mgr


class ServiceUser:
    __services = None

    @property
    def services(self):
        if self.__services is None:
            self.__services = ServiceManager.default()
        return self.__services

    @services.setter
    def services(self, value):
        assert isinstance(value, ServiceManager)
        self.__services = value


class Application(ServiceUser):

    @staticmethod
    def help(parser):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()
