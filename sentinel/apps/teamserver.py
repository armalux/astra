from ..framework import Application

class TeamserverApplication(Application):
    @staticmethod
    def help(parser):
        '''
        A team server, from which to launch all operations.
        '''
        parser.add_argument('-a', '--address', help='The address to which to bind, default is all.', default='0.0.0.0')
        parser.add_argument('-p', '--port', help='The port to bind to, default is random.', default=0)

    def run(self):
        pass
