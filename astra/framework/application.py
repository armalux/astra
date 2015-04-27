from .service import ServiceUser


class Application(ServiceUser):

    @staticmethod
    def help(parser):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()
