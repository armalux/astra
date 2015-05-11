__author__ = 'Eric Johnson'
from . import ConsoleCommand


class HelpCommand(ConsoleCommand):
    _name = 'help'

    @staticmethod
    def help(parser):
        """
        Display this message and return.
        """

    def run(self):
        headers = ('Name', 'Description')
        rows = [(command.name, command.description) for command in self.console.commands.values()]
        self.console.print_table(headers, rows)
