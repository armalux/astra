__author__ = 'Eric Johnson'
from . import ConsoleCommand
import binascii


class RandomCommand(ConsoleCommand):
    @classmethod
    def help(cls, parser):
        """
        Generate random, base64 encoded data, and print it to the command line.
        """
        parser.add_argument('length', help='Length of the data to generate.', type=int)

    def run(self):
        data = self.services.random.bytes(self.length)
        self.console.print(binascii.b2a_base64(data).decode('ascii').strip())
