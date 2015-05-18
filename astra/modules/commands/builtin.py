author = 'Eric Johnson'
uri = 'modules.commands.builtin'
name = 'Astra built-in console commands.'
description = 'Adds the default console commands.'


from astra.framework.module import CommandComponent
import binascii


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


class ReloadCommand(CommandComponent):
    @classmethod
    def help(cls, parser):
        """
        Reload modules.
        """

    def run(self):
        self.services.module.load()
        self.console.print('[=] Loaded {0} commands.'.format(len(self.console.commands)))


class SearchCommand(CommandComponent):
    phrase = None

    @staticmethod
    def help(parser):
        """
        Search components and modules for a specific phrase.
        """
        parser.add_argument('phrase', help='The phrase to search for.', type=str.lower)

    def run(self):
        headers = ('Module', 'Name', 'Description', 'Author')
        rows = []
        for module in self.services.module.modules.values():
            if self.phrase in module.name.lower() or \
               self.phrase in module.uri.lower() or \
               self.phrase in module.description.lower() or \
               self.phrase in module.author.lower():
                rows.append((module.uri, module.name, module.description, module.author))

        if rows:
            rows = sorted(rows, key=lambda row: row[0].lower())
            self.console.print_table(headers, rows)

        headers = ('Command', 'Description')
        rows = []
        for component in self.services.module.components['command'].values():
            if self.phrase in component.name.lower() or \
               self.phrase in component.description.lower():
                rows.append((component.name, component.description))

        if rows:
            rows = sorted(rows, key=lambda row: row[0].lower())
            self.console.print_table(headers, rows)
