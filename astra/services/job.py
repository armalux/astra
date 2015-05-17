__author__ = 'Eric Johnson'
from ..framework.job import JobManager
from ..framework.service import LazySingletonServiceProvider

provider = LazySingletonServiceProvider('job', JobManager)
