__author__ = 'Eric Johnson'
from . import ConsoleCommand


class ShutdownCommand(ConsoleCommand):
    @classmethod
    def help(cls, parser):
        """
        Stop the team server.
        """

    def run(self):
        exit(0)
