from ..framework.service import LazySingletonServiceProvider
from ..framework.router import Router

provider = LazySingletonServiceProvider('router', Router)
