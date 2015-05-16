__author__ = 'Eric Johnson'
import threading
from ..framework.service import SingletonServiceProvider

provider = SingletonServiceProvider('session', threading.local())
