import os


class MungerException(Exception):
    pass


class Munger:
    """
    Will alter a byte string to make it unreadable, but easily reversible.
    Nothing here is "cryptographically secure", but helps fight automated
    intrusion/malware detection systems.
    """

    @staticmethod
    def xor(data, key):
        """
        XOR a bytearray or bytes object against a single byte key.
        """
        assert isinstance(key, int)
        assert isinstance(data, (bytes, bytearray))

        if not len(data):
            raise MungerException('Data must not be zero length.')

        if key > 256 or key < 0:
            raise MungerException('Key must be 0-255')

        table = bytes([key ^ i for i in range(0, 256)])

        # noinspection PyUnresolvedReferences
        return data.translate(table)

    @staticmethod
    def multi_byte_xor(data, key):
        """
        XOR a bytearray or bytes object against a multi byte key.
        """
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

    @staticmethod
    def rolling_xor(data, key):
        """
        Perform a rolling XOR in a bytes or bytearray object.
        """
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
            data[i] = data[i] ^ key
            key = new_k

        return bytes(data)

    @staticmethod
    def multi_byte_rolling_xor(data, key):
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

    @staticmethod
    def rotating_xor(data, key, bits=3):
        """
        XOR a bytearray or bytes object, performing a 8-bit bitwise right rotation by 'bits'.
        """
        assert isinstance(data, (bytes, bytearray))
        assert isinstance(key, int)

        if not len(data):
            raise MungerException('Data must not be zero length.')

        if key < 0 or key > 255:
            raise MungerException('Key must be 0-255.')

        if isinstance(data, bytes):
            data = bytearray(data)

        for i in range(len(data)):
            data[i] ^= key
            key = ((key >> bits) | (key << (8 - bits) & 0xFF))

        return data

    @staticmethod
    def multi_byte_rotating_xor(data, key, bits=3):
        """
        XOR a bytearray or bytes objects with a multibyte key, while rotating each byte of the key.
        """
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
        key = bytearray(os.urandom(4))
        data = self.multi_byte_rotating_xor(data, key)
        return key + data

    def unmunge(self, data):
        return self.multi_byte_rotating_xor(data[4:], data[:4])
