__author__ = 'Eric Johnson'
from ..framework.application import Application


class ConsoleApplication(Application):
    @staticmethod
    def help(parser):
        """
        Launch an instance of the astra console.
        """
        parser.add_argument('host', help='Host to connect to in the form [hostname|ip]:[port]',
                            default='127.0.0.1:1337')

    def run(self):
        pass
