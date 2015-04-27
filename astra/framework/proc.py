import os


class Callback:
    def __init__(self, function, *args, **kwargs):
        self.__function = function
        self.__args = args
        self.__kwargs = kwargs

    def run(self):
        return self.__function(*self.__args, **self.__kwargs)

    def call(self, *args, **kwargs):
        return self.__function(*args, **kwargs)

    def fork(self, *args, **kwargs):
        return Forker(self).fork(*args, **kwargs)

    def __mul__(self, number):
        assert isinstance(number, int)
        if number == 0:
            return []

        return [self for x in range(0, number)]


class Forker:
    def __init__(self, *callbacks):
        for callback in callbacks:
            assert isinstance(callback, Callback)

        self.__callbacks = callbacks

    def fork(self, daemonize=False, wait=True, exit_function=None):
        if exit_function is None:
            exit_function = exit

        pids = []
        for callback in self.__callbacks:
            pid = os.fork()
            if pid != 0:
                pids.append(pid)
                continue

            if daemonize:
                os.setsid()

            try:
                retval = callback.run()
                exit_function(retval)

            except Exception:
                exit(-1)

            finally:
                exit(0)

        if not daemonize and wait:
            for pid in pids:
                os.waitpid(pid, 0)

        return pids


