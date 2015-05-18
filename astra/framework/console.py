__author__ = 'Eric Johnson'
import re
import argparse
import shlex
import io
import traceback
import readline
from ..framework.service import ServiceUser


class HelpAction(argparse.Action, ServiceUser):
    def __call__(self, parser, namespace, values, option_string=None):
        help_message = io.StringIO('')
        parser.print_help(file=help_message)
        self.services.session.console.print(help_message.getvalue())
        raise HelpActionAbort()


class HelpActionAbort(Exception):
    pass


class ConsoleCommandMeta(type):
    _name = None
    _parser = None

    @property
    def name(cls):
        if cls._name is None:
            formatter = re.compile(r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
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
            cls._parser = argparse.ArgumentParser(prog=cls.name, description=cls.description, add_help=False)
            cls._parser.add_argument('-h', '--help', action=HelpAction, nargs=0)
            cls.help(cls._parser)
        return cls._parser

    def help(cls, parser):
        raise NotImplementedError()


class ConsoleCommand(metaclass=ConsoleCommandMeta):
    def __init__(self, console, options):
        self.console = console
        for opt_name, opt_value in options.__dict__.items():
            setattr(self, opt_name, opt_value)

    def run(self):
        raise NotImplementedError()


class Console(ServiceUser):
    def __init__(self, client):
        self.client = client

    @property
    def commands(self):
        return self.services.module.components['command']

    def run(self, line):
        try:
            parts = shlex.split(line, posix=True)
        except ValueError:
            return

        if not parts:
            return

        if parts[0] not in self.commands:
            self.print('No such command.')
            return

        try:
            options = self.commands[parts[0]].parser.parse_args(parts[1:])

        except HelpActionAbort:
            return

        except SystemExit:
            self.print('Bad syntax, try "{0} -h".'.format(parts[0]))
            self.print(self.commands[parts[0]].parser.format_usage().strip())
            return

        except argparse.ArgumentError:
            return

        self.commands[parts[0]](self, options).run()

    def print(self, msg):
        if not isinstance(msg, str):
            msg = repr(msg)
        self.write(msg + '\n')

    def write(self, data):
        data = data.encode('utf-8')
        self.client.send_message(b'\x00' + data)

    def prompt(self, msg):
        msg = msg.encode('utf-8')
        self.client.send_message(b'\x01' + msg)
        return self.client.recv_message().decode('utf-8')

    def print_traceback(self, exception):
        assert isinstance(exception, Exception)

        traceback_list = traceback.extract_tb(exception.__traceback__)
        del traceback_list[:1]
        lines = traceback.format_list(traceback_list)
        if lines:
            lines.insert(0, "Traceback (most recent call last):\n")
        lines.extend(traceback.format_exception_only(exception.__class__, exception))
        self.print(''.join(lines))

    @staticmethod
    def get_csi_sequence(*sgr_codes):
        if not len(sgr_codes):
            return ''
        return '\x1b[{codes}m'.format(codes=';'.join([str(code) for code in sgr_codes]))

    def apply_sgr_codes(self, *sgr_codes):
        self.client.send_message(self.get_csi_sequence(*sgr_codes))

    def stylize(self, text, *sgr_codes, **kwargs):
        text = '{csi}{text}{reset}'.format(csi=self.get_csi_sequence(*sgr_codes),
                                           text=text, reset=self.get_csi_sequence(0))
        if not kwargs.get('print', False):
            return text
        self.client.send_message(text)

    def red(self, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(31)
        return self.stylize(text, *sgr_codes)

    def green(self, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(32)
        return self.stylize(text, *sgr_codes)

    def yellow(self, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(33)
        return self.stylize(text, *sgr_codes)

    def blue(self, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(34)
        return self.stylize(text, *sgr_codes)

    def magenta(self, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(35)
        return self.stylize(text, *sgr_codes)

    def cyan(self, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(36)
        return self.stylize(text, *sgr_codes)

    def white(self, text, *sgr_codes):
        sgr_codes = set(sgr_codes)
        sgr_codes.add(37)
        return self.stylize(text, *sgr_codes)

    def print_table(self, headers, rows, indent=3, column_padding=2):
        ljust = [len(header) for header in headers]
        for row in rows:
            for i, column in enumerate(row):
                ljust[i] = max(len(column), ljust[i])

        ljust = [i + column_padding for i in ljust]
        left_padding = indent * ' '
        header_line = ''.join([header.ljust(ljust[i]) for i, header in enumerate(headers)])
        separator_line = ''.join([('-'*len(header)).ljust(ljust[i]) for i, header in enumerate(headers)])

        self.print('')
        self.print(self.green(left_padding + header_line, 1))
        self.print(self.green(left_padding + separator_line, 1))

        for row in rows:
            content = ''.join([cell.ljust(ljust[i]) for i, cell in enumerate(row)])
            self.print(left_padding + content)

        self.print('')
