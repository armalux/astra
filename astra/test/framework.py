import unittest
import os
import random
import base64
import binascii
from ..framework.random import Random
from ..framework.munge import Munger, MungerException
from ..framework.service import ServiceManager


__all__ = ['TestRandomGenerator', 'TestMunger', 'TestServer']


class TestRandomGenerator(unittest.TestCase):
    def test_system_random(self):
        self.assertTrue(isinstance(self.random.system_random, random.SystemRandom))

    def test_bytes_length(self):
        for expected_length in range(1,1000):
            data = self.random.bytes(expected_length)
            self.assertTrue(len(data) == expected_length)

    def test_bytes_avoid(self):
        for expected_length in range(1,1000):
            avoid_bytes = os.urandom(10)
            data = self.random.bytes(expected_length, avoid=avoid_bytes)
            for b in avoid_bytes:
                self.assertFalse(b in data)

    def test_bytes_zero_length(self):
        data = self.random.bytes(0)
        self.assertTrue(len(data) == 0)

    def test_integer(self):
        minimum, maximum = 0, 100
        i = self.random.integer(minimum, maximum)
        self.assertTrue(minimum <= i <= maximum)

        minimum, maximum = 0, 100
        i = self.random.integer(maximum)
        self.assertTrue(minimum <= i <= maximum)

        minimum, maximum = 0, 2**32
        i = self.random.integer()
        self.assertTrue(minimum <= i <= maximum)

    def test_sample_length(self):
        for expected_length in range(1, 1000):
            data = self.random.sample(os.urandom(100), expected_length)
            self.assertTrue(len(data) == expected_length)

    def test_sample_return_type(self):
        data = self.random.sample(os.urandom(10), 100)
        self.assertTrue(isinstance(data, bytes))

    def test_sample_avoid(self):
        length = 100

        for i in range(0,1000):
            avoid = os.urandom(10)
            data = self.random.sample(os.urandom(1000), length, avoid)
            for a in avoid:
                self.assertFalse(a in data)

    def test_printable_length(self):
        for expected_length in range(1, 1000):
            data = self.random.printable(expected_length)
            self.assertTrue(len(data) == expected_length)
            for d in data:
                self.assertTrue(31 < d < 127)

    def test_printable_avoid(self):
        for expected_length in range(1, 1000):
            avoid_bytes = bytes(random.sample(range(32, 127), 10))
            data = self.random.printable(expected_length, avoid=avoid_bytes)
            for b in avoid_bytes:
                self.assertFalse(b in data)

    def test_printable_zero_length(self):
        data = self.random.printable(0)
        self.assertTrue(len(data) == 0)

    def test_base64_decodable(self):
        for length in range(0, 1000):
            data = self.random.base64(length, decodable=True)
            self.assertTrue(len(data) >= length)
            try:
                base64.b64decode(data.decode('ascii'))
            except:
                print(data)
                raise

    def test_hex_decodable(self):
        for length in range(0, 1000):
            data = self.random.hex(length, decodable=True)
            self.assertTrue(len(data) >= length)
            binascii.unhexlify(data)

    def setUp(self):
        self.random = Random()

    def tearDown(self):
        self.random = None


class TestMunger(unittest.TestCase):
    def setUp(self):
        self.munger = Munger()

    def tearDown(self):
        self.munger = None

    def test_xor(self):
        plain_text = os.urandom(4096)
        key = os.urandom(1)[0]

        cipher_text = self.munger.xor(plain_text, key)
        self.assertFalse(cipher_text == plain_text)
        self.assertTrue(len(cipher_text) == len(plain_text))

        for i in range(len(plain_text)):
            self.assertTrue(cipher_text[i] ^ key == plain_text[i])

        with self.assertRaises(MungerException):
            self.munger.xor(b'', key)

        with self.assertRaises(MungerException):
            self.munger.xor(plain_text, 1000)

    def test_multi_byte_xor(self):
        plain_text = os.urandom(4096)
        key = os.urandom(11)

        cipher_text = self.munger.multi_byte_xor(plain_text, key)
        self.assertFalse(cipher_text == plain_text)
        self.assertTrue(len(cipher_text) == len(plain_text))

        k = 0
        for i in range(len(cipher_text)):
            if k == len(key):
                k = 0
            self.assertTrue(cipher_text[i] ^ key[k] == plain_text[i])
            k += 1

        plain_text_test = self.munger.multi_byte_xor(cipher_text, key)
        self.assertTrue(plain_text_test == plain_text)

    def test_rotating_xor(self):
        plain_text = os.urandom(4096)
        key = os.urandom(1)[0]

        cipher_text = self.munger.rotating_xor(plain_text, key)
        self.assertFalse(cipher_text == plain_text)
        self.assertTrue(len(cipher_text) == len(plain_text))

        plain_text_test = self.munger.rotating_xor(cipher_text, key)
        self.assertTrue(plain_text_test == plain_text)

    def test_multi_byte_rotating_xor(self):
        plain_text = os.urandom(4096)
        key = os.urandom(11)

        cipher_text = self.munger.multi_byte_rotating_xor(plain_text, key)
        self.assertFalse(cipher_text == plain_text)
        self.assertTrue(len(cipher_text) == len(plain_text))

        plain_text_test = self.munger.multi_byte_rotating_xor(cipher_text, key)
        self.assertTrue(plain_text_test == plain_text)

    def test_munge(self):
        plain_text = os.urandom(4096)

        munged = self.munger.munge(plain_text)
        self.assertFalse(munged == plain_text)

        unmunged = self.munger.unmunge(munged)
        self.assertTrue(unmunged == plain_text)


class TestServer(unittest.TestCase):
    def test_load(self):
        services = ServiceManager()
        services.load()
        services.module.load()
