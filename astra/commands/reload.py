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
        for name, module in sys.modules.items():
            if name.startswith('astra.commands.'):
                self.console.print('Reloading module "' + name + '".')
                reload(module)
        self.console.reload_commands()
