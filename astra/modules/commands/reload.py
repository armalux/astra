author = 'Eric Johnson'
uri = 'io.armalux.astra.modules.commands.reload'
name = 'Astra console reload.'
description = 'Adds the reload command to the console.'


from astra.framework.module import CommandComponent


class ReloadCommand(CommandComponent):
    @classmethod
    def help(cls, parser):
        """
        Reload modules.
        """

    def run(self):
        self.services.module.load()
        self.console.print('[=] Loaded {0} commands.'.format(len(self.console.commands)))
