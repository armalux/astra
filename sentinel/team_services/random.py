import os
import random

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



