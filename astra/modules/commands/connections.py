author = 'Eric Johnson'
uri = 'io.armalux.astra.modules.commands.connections'
name = 'Astra console connections command.'
description = 'Adds the connections command to the console.'


from astra.framework.module import CommandComponent


class ConnectionsCommand(CommandComponent):
    @staticmethod
    def help(parser):
        """
        List active connections.
        """

    def run(self):
        pass

