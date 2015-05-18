author = 'Eric Johnson'
uri = 'io.armalux.astra.modules.commands.python'
name = 'Astra python console'
description = 'Adds the python console command'

from astra.framework.module import CommandComponent
from astra.framework.console import Console
from code import InteractiveConsole
from types import ModuleType
import sys
import inspect
import astra


class PassThroughModule(ModuleType):
    def __init__(self, real_module):
        assert isinstance(real_module, ModuleType)

        super().__init__(real_module.__name__)
        self._real_module = real_module

    # noinspection PyCallByClass
    def __getattr__(self, item):
        if item.startswith('__'):
            return object.__getattribute__(self, item)

        for member_name, member in inspect.getmembers(self, item):
            if member_name == item:
                return object.__getattribute__(self, item)

        if hasattr(self._real_module, item):
            return getattr(self._real_module, item)

        raise AttributeError(item)

    # noinspection PyCallByClass
    def __setattr__(self, item, value):
        object.__setattr__(self, item, value)


class FakeSys(PassThroughModule):
    def __init__(self, real_module, console):
        assert isinstance(real_module, ModuleType)
        assert isinstance(console, Console)
        super().__init__(real_module)
        self.stdout = console
        self.stderr = console
        self.__stdout__ = console
        self.__stderr__ = console


class PythonConsole(InteractiveConsole):
    def __init__(self, console, local=None):
        super().__init__(locals=local)
        self.console = console

    def raw_input(self, prompt=""):
        return self.console.prompt(prompt)

    def write(self, data):
        self.console.write(data)


class PythonCommand(CommandComponent):
    @classmethod
    def help(cls, parser):
        """
        Launch a python console.
        """

    def run(self):
        # noinspection PyTypeChecker
        local = {"__name__": "__console__",
                 "__doc__": None,
                 'sys': FakeSys(sys, self.console),
                 'print': self.console.print,
                 'input': self.console.prompt,
                 'astra': astra}
        console = PythonConsole(self.console, local)
        console.interact()
