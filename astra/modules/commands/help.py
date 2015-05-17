author = 'Eric Johnson'
uri = 'io.armalux.astra.modules.commands.help'
name = 'Astra console help.'
description = 'Adds the help command to the console.'


from astra.framework.module import CommandComponent


class HelpCommand(CommandComponent):
    @staticmethod
    def help(parser):
        """
        Display a list of commands and return.
        """

    def run(self):
        headers = ('Name', 'Description')
        rows = [(command.name, command.description) for command in self.console.commands.values()]
        rows = sorted(rows, key=lambda row: row[0].lower())
        self.console.print_table(headers, rows)
