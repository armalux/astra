from ..framework.service import LazySingletonServiceProvider
from ..framework.random import Random

provider = LazySingletonServiceProvider('random', Random)
