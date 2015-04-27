import re
import argparse
import sys
import shlex
import readline
from .service import ServiceUser


class ConsoleCommandMeta(type):
    _name = None
    _parser = None

    @property
    def name(cls):
        if cls._name is None:
            formatter = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
            name = formatter.sub(r'_\1', cls.__name__).lower().split('_')
            if name[-1] == 'command':
                name = name[:-1]
            cls._name = '_'.join(name)
        return cls._name

    @property
    def description(cls):
        return cls.help.__doc__.strip()

    @property
    def parser(cls):
        if cls._parser is None:
            cls._parser = argparse.ArgumentParser(prog=cls.name, description=cls.description)
            cls.help(cls._parser)
        return cls._parser

    def help(cls, parser):
        raise NotImplementedError()


class ConsoleCommand(ServiceUser, metaclass=ConsoleCommandMeta):
    def __init__(self, console, options):
        self.console = console
        for opt_name, opt_value in options.__dict__.items():
            setattr(self, opt_name, opt_value)

    def run(self):
        raise NotImplementedError()


class ConsoleExitCommand(ConsoleCommand):
    _name = 'exit'

    @staticmethod
    def help(parser):
        '''
        Exit this console.
        '''

    def run(self):
        self.console.exit()


class ConsoleHelpCommand(ConsoleCommand):
    _name = 'help'

    @staticmethod
    def help(parser):
        '''
        Display this message and return.
        '''

    def run(self):
        headers = ('Name', 'Description')
        rows = [(command.name, command.description) for command in self.console._commands.values()]
        self.console.print_table(headers, rows)


class Console:
    _commands = None
    _parser = None
    _prompt = '>'
    input_sgr_codes = None
    _exiting = False

    def __init__(self, commands = []):
        assert isinstance(commands, (list,tuple))
        self._commands = {}
        self.input_sgr_codes = []
        self.history = []

        self.add_command(ConsoleExitCommand)
        self.add_command(ConsoleHelpCommand)

        for command in commands:
            self.add_command(command)

    @property
    def prompt(self):
        return self._prompt

    @prompt.setter
    def prompt(self, value):
        assert isinstance(value, str)
        self._prompt = value

    def add_command(self, command, override=False):
        assert issubclass(command, ConsoleCommand)
        if not override and command.name in self._commands:
            raise ValueError('{0} already exists in this console.'.format(command.name))
        self._commands[command.name] = command

    def exit(self):
        self._exiting = True

    @classmethod
    def input(cls, prompt='', *sgr_codes):
        prompt = '{prompt} {csi}'.format(prompt=prompt, csi=cls.get_csi_sequence(*sgr_codes))

        try:
            sys.stdout.flush()
            buf = input(prompt)
        finally:
            cls.apply_sgr_codes(0)

        return buf

    def run_line(self, line):
        parts = shlex.split(line, posix=True)
        self.history.append(line)
        readline.clear_history()
        ret = self.run_command(parts)
        readline.clear_history()

        for entry in self.history:
            readline.add_history(entry)

        return ret

    def run_command(self, parts):
        if parts[0] in self._commands:
            try:
                options = self._commands[parts[0]].parser.parse_args(parts[1:])
            except SystemExit:
                options = None

            except argparse.ArgumentError as e:
                options = None

            if options is None:
                return False

            self._commands[parts[0]](self, options).run()

        else:
            print('No such command.')
            return False

        return True

    def run(self, cmd=None):
        while True:
            if self._exiting:
                break

            try:
                line = self.input(self.prompt, *self.input_sgr_codes)

            except (KeyboardInterrupt, EOFError):
                print('exit\nGoodbye.')
                break

            if not len(line):
                continue

            self.run_line(line)

    @staticmethod
    def get_csi_sequence(*sgr_codes):
        if not len(sgr_codes):
            return ''
        return '\x1b[{codes}m'.format(codes=';'.join([str(code) for code in sgr_codes]))

    @classmethod
    def apply_sgr_codes(cls, *sgr_codes):
        sys.stdout.write(cls.get_csi_sequence(*sgr_codes))
        sys.stdout.flush()

    @classmethod
    def stylize(cls, text, *sgr_codes, **kwargs):
        text = '{csi}{text}{reset}'.format(csi=cls.get_csi_sequence(*sgr_codes), text=text, reset=cls.get_csi_sequence(0))
        if not kwargs.get('print', False):
            return text
        sys.stdout.write(text)

    @classmethod
    def red(cls, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(31)
        return cls.stylize(text, *sgr_codes)

    @classmethod
    def green(cls, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(32)
        return cls.stylize(text, *sgr_codes)

    @classmethod
    def yellow(cls, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(33)
        return cls.stylize(text, *sgr_codes)

    @classmethod
    def blue(cls, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(34)
        return cls.stylize(text, *sgr_codes)

    @classmethod
    def magenta(cls, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(35)
        return cls.stylize(text, *sgr_codes)

    @classmethod
    def cyan(cls, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(36)
        return cls.stylize(text, *sgr_codes)

    @classmethod
    def white(cls, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(37)
        return cls.stylize(text, *sgr_codes)

    @classmethod
    def print_table(cls, headers, rows, indent=3, column_padding=2):
        ljust = [len(header) for header in headers]
        for row in rows:
            for i,column in enumerate(row):
                ljust[i] = max(len(column), ljust[i])

        ljust = [i + column_padding for i in ljust]
        left_padding = indent * ' '
        header_line = ''.join([header.ljust(ljust[i]) for i,header in enumerate(headers)])
        separator_line = ''.join([('-'*len(header)).ljust(ljust[i]) for i,header in enumerate(headers)])

        print('')
        print(cls.green(left_padding + header_line, 1))
        print(cls.green(left_padding + separator_line, 1))

        for row in rows:
            content = ''.join([cell.ljust(ljust[i]) for i,cell in enumerate(row)])
            print(left_padding + content)

        print('')



