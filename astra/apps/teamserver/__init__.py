from ...framework.application import Application
from ...framework.teamserver.handler import TeamServerHandler
from ...framework.service import SingletonServiceProvider
from tornado import web, ioloop, httpserver, gen
import os


class TeamserverApplication(Application):
    @staticmethod
    def help(parser):
        '''
        A team server, from which to launch all operations.
        '''
        parser.add_argument('-a', '--address', help='The address to which to bind, default is all.', default='0.0.0.0')
        parser.add_argument('-p', '--port', help='The port to bind to, default is random.', default=8080, type=int)
        parser.add_argument('-d', '--debug', help='Have the Tornado application work in debug mode.', action='store_true', default=False)

    def run(self):
        static_path = os.path.join(os.path.dirname(__file__), 'static')

        app = web.Application([
            ('/ws', TeamServerHandler),
            ('/(console.html)', web.StaticFileHandler, {'path': static_path}),
            ('/static/(.*)', web.StaticFileHandler, {'path': static_path})
        ], debug=self.debug)

        server = httpserver.HTTPServer(app)
        self.services.register(SingletonServiceProvider('teamserver', server))
        server.listen(self.port, self.address)

        @gen.coroutine
        def display_running_message():
            print('Running.')

        ioloop.IOLoop.instance().add_callback(display_running_message)
        print('Starting Astra Team Server on {0}:{1}...'.format(self.address, self.port))
        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            ioloop.IOLoop.instance().stop()
            print('Goodbye.')

