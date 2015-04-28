from ..framework.service import SingletonServiceProvider
from ..framework.socket import Socket


provider = SingletonServiceProvider('socket', Socket)
