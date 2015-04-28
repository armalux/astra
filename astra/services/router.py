from ..framework.service import LazySingletonServiceProvider
from ..framework.router import Router

Router.__provider__ = LazySingletonServiceProvider('router', Router)
