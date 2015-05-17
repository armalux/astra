__author__ = 'Eric Johnson'
from ..framework.module import ModuleManager
from ..framework.service import SingletonServiceProvider
from os.path import dirname, realpath, join


services_dir = dirname(realpath(__file__))

mm = ModuleManager()
mm.add_directory(join(dirname(services_dir), 'modules'))
mm.load()

provider = SingletonServiceProvider('module', mm)
