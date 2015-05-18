from ..framework.application import Application
import unittest


class TestApplication(Application):
    """
    Run the unit tests for astra
    """
    test = None

    @staticmethod
    def help(parser):
        parser.add_argument('-t', '--test', help='A package, module or fully qualified class name.',
                            default='astra.test')
        parser.add_argument('-v', '--verbose', help='Display verbose output.', action='store_true', default=False)

    def run(self):
        unittest.main(module='astra.test', argv=[self.test], verbosity=2)
