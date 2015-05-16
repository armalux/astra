__author__ = 'Eric Johnson'
from . import ConsoleCommand
import sys
from importlib import reload


class ReloadCommand(ConsoleCommand):
    @classmethod
    def help(cls, parser):
        """
        Reload modules.
        """

    def run(self):
        count = 0
        errors = 0
        for name, module in sys.modules.items():
            if name.startswith('astra.commands.'):
                try:
                    reload(module)

                except AttributeError:
                    pass

                except SyntaxError as e:
                    errors += 1
                    self.console.print(
                        self.console.red('[-] Failed to reload module "' + name + '" due to syntax error:'))
                    self.console.print_traceback(e)
                else:
                    count += 1
                    self.console.print('[+] Reloading module "' + name + '"...')

        self.console.print('[=] Reloaded {0} modules with {1} errors.'.format(count, errors))
        self.console.reload_commands()
        self.console.print('[=] Loaded {0} commands.'.format(len(self.console.commands)))
