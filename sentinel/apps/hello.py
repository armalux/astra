from ..framework import Application, ServiceUser, SingletonServiceProvider


class Greeter(ServiceUser):
    '''
    A class, who's instances may greet a specific noun.
    '''

    def __init__(self, name):
        assert isinstance(name, str)
        self.name = name.capitalize()

    def greet(self):
        print('Greetings and salutations, {name}!'.format(name=self.name))


class HelloApplication(Application):
    '''
    Say hello!
    '''
    def __init__(self):
        '''
        Use this to perform any application initialization, such as registering custom services.
        '''
        self.services.register(SingletonServiceProvider('greeter', Greeter, self.name))

    @staticmethod
    def help(parser):
        '''
        Say "Hello, <name>!" as required.
        '''
        parser.add_argument('name', help='To whom to say hello.')

    def run(self):
        self.services.greeter.greet()
