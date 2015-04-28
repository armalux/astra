from ..framework.service import LazySingletonServiceProvider
from ..framework.munge import Munger

provider = LazySingletonServiceProvider('munge', Munger)
