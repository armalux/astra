import code
import sentinel
from sentinel.framework import ConsoleCommand

class Hello(ConsoleCommand):
    @staticmethod
    def help(parser):
        '''
        Greet a fellow noun!
        '''
        parser.add_argument('name', help='Who to greet.')

    def run(self):
        print('Hello, {name}!'.format(name=self.name))

class Python(ConsoleCommand):
    @staticmethod
    def help(parser):
        '''
        Drop to a python or pdb shell.
        '''
        parser.add_argument('-d', '--debug', help='Drop to a pdb shell.', default=False, action='store_true')

    def run(self):
        if not self.debug:
            self.python()
        else:
            import pdb
            pdb.set_trace()

    def python(self):
        def return_function(code=None):
            raise SystemExit()

        local = {
            'sentinel': sentinel,
            'exit': return_function,
            'quit': return_function
        }

        try:
            code.interact(local=local)

        except SystemExit:
            pass

        except Exception as e:
            print(self.console.red(str(e)))
