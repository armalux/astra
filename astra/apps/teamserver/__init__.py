from ...framework.application import Application
from ...framework.teamserver.handler import TeamServerHandler
from ...framework.service import SingletonServiceProvider
from ...framework.proc import Callback
from tornado import web, ioloop, httpserver, gen
import os
import time


class TeamserverApplication(Application):
    def __init__(self):
        self._web_server_thread = None
        loop = ioloop.IOLoop()
        self._web_server_thread = Callback(self.run_web_server,
                                           loop, self.address, self.port,
                                           self.debug).spawn(stop=loop.stop, start=False)

    @staticmethod
    def help(parser):
        """
        A team server, from which to launch all operations.
        """
        parser.add_argument('-a', '--address', help='The address to which to bind, default is all.', default='0.0.0.0')
        parser.add_argument('-p', '--port', help='The port to bind to, default is random.', default=8080, type=int)
        parser.add_argument('-d', '--debug', help='Have the Tornado application work in debug mode.',
                            action='store_true', default=False)

    def start_web_server(self):
        """
        Start the web server in a thread and return.
        :return: None
        """
        self._web_server_thread.start()

    def stop_web_server(self):
        """
        Stop the web server and return.
        :return: None
        """
        self._web_server_thread.stop()

    def run_web_server(self, loop, address, port, debug=False):
        """
        Run the web server.

        :param loop: an tornado.ioloop.IOLoop instance to use.
        :param address: the ip address of the interface to bind to.
        :param port: the tcp port to listen on
        :param debug: run in debug mode
        :return: None
        """
        static_path = os.path.join(os.path.dirname(__file__), 'static')

        app = web.Application([
            ('/ws', TeamServerHandler),
            ('/(console.html)', web.StaticFileHandler, {'path': static_path}),
            ('/static/(.*)', web.StaticFileHandler, {'path': static_path})
        ], debug=debug)

        server = httpserver.HTTPServer(app)
        self.services.register(SingletonServiceProvider('teamserver', server))
        server.listen(port, address)

        @gen.coroutine
        def display_running_message(self):
            print('Astra Team Web Server listening on {0}:{1}...'.format(self.address, self.port))

        # Add a message to show the port and address once the server has started.
        loop.add_callback(display_running_message, self)
        print('Starting Astra Team Web Server...')

        # Start the ioloop
        loop.start()

    def run(self):
        self.start_web_server()

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            self.stop_web_server()

        print('Goodbye.')
