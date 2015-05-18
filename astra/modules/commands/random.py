author = 'Eric Johnson'
uri = 'io.armalux.astra.modules.commands.random'
name = 'Astra console random.'
description = 'Adds the random command to the console.'


from astra.framework.module import CommandComponent
import binascii


class RandomCommand(CommandComponent):
    length = None

    @classmethod
    def help(cls, parser):
        """
        Generate random, base64 encoded data, and print it to the command line.
        """
        parser.add_argument('length', help='Length of the data to generate.', type=int)

    def run(self):
        data = self.services.random.bytes(self.length)
        self.console.print(binascii.b2a_base64(data).decode('ascii').strip())
