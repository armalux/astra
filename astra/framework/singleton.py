import threading


class SingletonMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instance


class Singleton(metaclass=SingletonMeta):
    pass


class ThreadSingletonMeta(type):
    _thread_local_storage = None

    def __call__(cls, *args, **kwargs):
        if cls._thread_local_storage is None:
            cls._thread_local_storage = threading.local()

        if not hasattr(cls._thread_local_storage, 'instance'):
            cls._thread_local_storage.instance = super(ThreadSingletonMeta, cls).__call__(*args, **kwargs)

        return cls._thread_local_storage.instance
