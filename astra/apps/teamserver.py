import time
from ..framework.application import Application
from astra.framework.server import TeamServer


class TeamserverApplication(Application):
    @staticmethod
    def help(parser):
        """
        A team server, from which to launch all operations.
        """

    def __init__(self):
        start = time.clock()
        # Load Services
        self.services.load()

        services_loaded = time.clock() - start

        # Load all modules.
        self.services.module.load()

        modules_loaded = time.clock() - services_loaded

        print('Services loaded in {0} ms.'.format(services_loaded*1000))
        print('Modules loaded in {0} ms.'.format(modules_loaded*1000))

    def run(self):
        ts = TeamServer()
        ts.start()

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print('Caught interrupt, exiting...')

        finally:
            ts.stop()

        print('Goodbye.')
