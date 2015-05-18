"""
This file contains classes to handle threading, callbacks, and forking.
"""
import os
import threading


class Threader(threading.Thread):
    """
    If the first argument of target is 'threader', will pass a copy of the threader object to the target.
    Will also call self.stop_callback before joining the thread.

    The target function may call threader.exiting.wait() to wait to be told to exit, or threader.exiting.is_set() to
    check if the thread is supposed to be exiting.
    """
    def __init__(self, target, *args, **kwargs):
        arg_names = target.__code__.co_varnames[:target.__code__.co_argcount]
        if arg_names and arg_names[0] == 'threader':
            args = tuple([self] + list(args))

        super().__init__(target=target, args=args, kwargs=kwargs)
        self.exiting = threading.Event()
        self._stop_callback = lambda: None

    @property
    def stop_callback(self):
        """
        A callback to be called when stopping the thread.
        """
        return self._stop_callback

    @stop_callback.setter
    def stop_callback(self, value):
        assert callable(value)
        self._stop_callback = value

    def start(self):
        """
        Starts the thread

        :return: False if the thread is already running, True if the thread started.
        """
        if super().isAlive():
            return False

        self.exiting.clear()
        super().start()

        return True

    def stop(self, timeout=None):
        """
        Will ask the thread to cleanup (by setting self.exiting), then joins the thread.

        :param timeout: Max seconds to wait for the thread to exit before giving up, as a float.
        :return: False if the thread failed to exit, True if the thread exited, None if the thread was not running.
        """
        if not super().isAlive():
            return None

        self.stop_callback()
        self.exiting.set()
        super().join(timeout=timeout)
        if super().isAlive():
            return False

        return True


class Callback:
    def __init__(self, function, *args, **kwargs):
        self._function = function
        self._args = args
        self._kwargs = kwargs

    def spawn(self, threader=False, stop=None, daemon=None, start=True):
        """
        Will spawn a thread to run the callback.

        :param threader: True to spawn a threader, this is good for threads that need to be told when to exit.
        :param stop: A function to call to stop the thread before joining it.
        :return: threading.Thread if threader is False, else astra.framework.proc.Threader
        """
        if stop is not None:
            threader = True

        if threader:
            thread = Threader(self._function, *self._args, **self._kwargs)
            if stop is not None:
                thread.stop_callback = stop
        else:
            thread = threading.Thread(target=self._function, args=self._args, kwargs=self._kwargs)

        if daemon is not None:
            thread.daemon = daemon

        if start:
            thread.start()

        return thread

    def __call__(self, *args, **kwargs):
        """
        Call the function for this callback, with custom args and kwargs.
        if no args or kwargs are provided, will use the default ones set in the constructor.

        :param args: Arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function
        :return: The function's return value.
        """
        if not args and not kwargs:
            return self._function(*self._args, **self._kwargs)
        else:
            return self._function(*args, **kwargs)

    def fork(self, *args, **kwargs):
        """
        Fork and run the callback, does not return in the child process.

        :param args: Arguments to pass to Forker.fork
        :param kwargs: Keyword arguments to pass to Forker.fork
        :return: The process id of the child
        """
        return Forker(self).fork(*args, **kwargs)[0]

    def __mul__(self, number):
        """
        Multiply the callback, getting a list.

        :param number: the number to multiply by, must be a positive integer
        :return: list containing a specified number of copies of this callback
        """
        assert isinstance(number, int) and number >= 0
        if number == 0:
            return []

        return [self for x in range(0, number)]


class Forker:
    def __init__(self, *callbacks):
        """
        :param callbacks: Callback objects to run
        """
        for callback in callbacks:
            assert isinstance(callback, Callback)

        self.__callbacks = callbacks

    def fork(self, daemonize=False, wait=True, exit_function=None):
        """
        Fork and run each Callback instance.

        :param daemonize: Become a daemon after forking, so we don't create zombies if we don't plan on waiting later.
        :param wait: If daemonize is False, will wait for each forked process to exit before returning.
        :param exit_function: A function to call after the callback has returned, will pass in the return value.
        :return: Does not return in the child process, in the parent it returns a list of process IDs.
        """
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

            # noinspection PyBroadException
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
