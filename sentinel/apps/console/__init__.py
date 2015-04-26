from ...framework import Application, Console, ConsoleCommand, SingletonObjectServiceProvider
import os
from importlib import import_module

class ConsoleApplication(Application):
    '''
    Launch the sentinel console.
    '''
    __command_directory = None

    def __init__(self):
        self.console = Console()
        self.console.prompt = '{prompt} >'.format(prompt=self.console.red('sentinel'))
        self.console.input_sgr_codes = [33]
        self.services.register(SingletonObjectServiceProvider('console', self.console))

    @staticmethod
    def help(parser):
        parser.add_argument('command', help='A command and it\'s operations and arguments to run, then exit.', nargs='*', default=None)

    @property
    def command_directory(self):
        if self.__command_directory is None:
            self.__command_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'commands')
        return self.__command_directory

    def load_commands(self):
        for fname in os.listdir(self.command_directory):
            if fname in ['__init__.py', '__main__.py', '__pycache__']:
                continue

            if os.path.isfile(os.path.join(self.command_directory, fname)):
                module_name, extension = os.path.splitext(fname)
                if extension != '.py':
                    continue
            else:
                module_name = fname

            module = import_module('.commands.{0}'.format(module_name), __name__)

            if hasattr(module, '__commands__'):
                command_class_names = module.__commands__
            else:
                command_class_names = []
                for name, value in module.__dict__.items():
                    if not isinstance(value, type) or  value is ConsoleCommand:
                        continue

                    if issubclass(value, ConsoleCommand):
                        command_class_names.append(name)

            for name in command_class_names:
                self.console.add_command(getattr(module, name))

    def run(self):
        self.load_commands()

        if len(self.command):
            self.console.run_command(self.command)
        else:
            self.console.run()
