author = 'Eric Johnson'
uri = 'io.armalux.astra.modules.commands.search'
name = 'Astra console search command.'
description = 'Adds the search command to the console.'


from astra.framework.module import CommandComponent


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
