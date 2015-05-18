import os
import random
import binascii
import math


# noinspection PyTypeChecker
class Random:
    """
    A set of relatively fast random data algorithms.
    """
    __system_random = None

    @property
    def system_random(self):
        """
        An instance of random.SystemRandom used by some operations, but not all, due to performance.
        """
        if self.__system_random is None:
            self.__system_random = random.SystemRandom()
        return self.__system_random

    @staticmethod
    def bytes(length, avoid=b''):
        """
        Gets secure random bytes, avoiding the bytes specified.
        """
        ret = b''
        avoid = bytes(set(avoid))
        while len(ret) != length:
            data = os.urandom(length - len(ret)).translate(None, avoid)
            ret += data

        return ret

    def integer(self, *args):
        """
        Generates a secure random integer
        integer() - min is 0, max is signed 32 bit max
        integer(max)
        integer(min, max)
        """
        if len(args) == 0:
            minimum, maximum = 0, 2 ** 32

        elif len(args) == 1:
            minimum, maximum = 0, args[0]

        elif len(args) == 2:
            minimum, maximum = args

        else:
            raise ValueError('Random.integer only accepts 0-2 arguments.')

        return self.system_random.randint(minimum, maximum)

    @staticmethod
    def sample(sequence, length, avoid=b''):
        """
        Select a random sample of bytes from the given sequence of bytes, avoiding those specified.
        The sample size may be larger than the sequence, and the selections may repeat.
        """
        assert isinstance(sequence, bytes) or isinstance(sequence, bytearray)
        sequence = bytearray(set(sequence))
        avoid = bytes(set(avoid))
        for a in avoid:
            while a in sequence:
                sequence.pop(sequence.find(a))
        return bytes([sequence[x % len(sequence)] for x in os.urandom(length)])

    @classmethod
    def printable(cls, length, avoid=b''):
        """
        Gets ascii printable-range secure random bytes, avoiding bytes specified.
        """
        return cls.sample(bytes(range(32, 127)), length, avoid)

    @classmethod
    def alphabetic(cls, length, avoid=b''):
        """
        Gets mixed-case alphabetic ascii secure random bytes.
        """
        return cls.sample(bytes(range(65, 91)) + bytes(range(97, 123)), length, avoid)

    @classmethod
    def alphabetic_lower(cls, length, avoid=b''):
        """
        Gets lower-case alphabetic ascii secure random bytes.
        """
        return cls.sample(bytes(range(97, 123)), length, avoid)

    @classmethod
    def alphabetic_upper(cls, length, avoid=b''):
        """
        Gets upper-case alphabetic ascii secure random bytes.
        """
        return cls.sample(bytes(range(65, 91)), length, avoid)

    @classmethod
    def numeric(cls, length, avoid=b''):
        """
        Gets numeric ascii secure random bytes.
        """
        return cls.sample(bytes(range(48, 58)), length, avoid)

    @classmethod
    def alphanumeric(cls, length, avoid=b''):
        """
        Gets mixed-case alphanumeric ascii secure random bytes.
        """
        return cls.sample(bytes(range(48, 58)) + bytes(range(65, 91)) + bytes(range(97, 123)), length, avoid)

    @classmethod
    def alphanumeric_lower(cls, length, avoid=b''):
        """
        Gets lower-case alphanumeric ascii secure random bytes.
        """
        return cls.sample(bytes(range(48, 58)) + bytes(range(97, 123)), length, avoid)

    @classmethod
    def alphanumeric_upper(cls, length, avoid=b''):
        """
        Gets upper-case alphanumeric ascii secure random bytes.
        """
        return cls.sample(bytes(range(48, 58)) + bytes(range(65, 91)), length, avoid)

    @classmethod
    def hex(cls, length, avoid=b'', decodable=True):
        """
        Returns a bytes string of random (upper-case) ascii hexadecimal characters.
        If decodable=True, will return a hex string >= the specified length that can be decoded into bytes
        If decodable=False, will return a hex string, exactly the specified length, not guarenteed to decode.
        """
        if decodable:
            if length < 2:
                length = 2
            if length % 2 != 0:
                length += 1

        return cls.sample(bytes(range(48, 58)) + bytes(range(65, 71)), length, avoid)

    @classmethod
    def base64(cls, length, avoid=b'', decodable=True):
        """
        Returns a bytes string of random ascii base-64 characters.
        If decodable=True, will create a decodable base64 string who's length is >= the specified length, may include
        avoid characters.
        If decodable=False, will create a bytes string of the exact length specified, but it may not decode.
        """
        if not decodable:
            return cls.sample(bytes(range(48, 58)) + bytes(range(65, 91)) + bytes(range(97, 123)) + b'+/', length,
                              avoid)

        return binascii.b2a_base64(cls.bytes(math.ceil(float(length) * (5.0 / 6.0))))
