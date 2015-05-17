__author__ = 'Eric Johnson'
from .proc import Callback
from threading import Event


class JobManager:
    def __init__(self):
        self._jobs = {}
        self._complete_callbacks = {}
        self._next_id = 0

    @property
    def next_id(self):
        with self._next_id as next_id:
            self._next_id += 1
            return next_id

    def _complete_job(self, job_id):
        if job_id not in self._jobs:
            raise ValueError('job_id not in jobs')

        job = self._jobs[job_id]
        del self._jobs[job_id]

        if job_id in self._complete_callbacks:
            try:
                self._complete_callbacks[job_id](job)
            finally:
                del self._complete_callbacks[job_id]

    def create(self, callback, on_complete=None):
        assert isinstance(callback, Callback)
        assert callable(on_complete) or on_complete is None

        job_id = self.next_id
        job = Job(callback, Callback(self._complete_job, job_id))
        self._jobs[job_id] = job

        if on_complete is not None:
            self._complete_callbacks[job_id] = on_complete

        job.run()
        return job


class Job:
    def __init__(self, callback, on_complete=None):
        assert isinstance(callback, Callback)
        self._callback = callback
        self.result = None
        self.exception = None
        self.on_complete = on_complete if on_complete is not None else lambda job: None
        self._ran = False

        self._event = Event()
        self._event.set()

    def wait(self):
        self._event.wait()

    @property
    def running(self):
        return not self._event.is_set()

    def _run(self):
        try:
            self.result = self._callback()

        except Exception as e:
            self.exception = e

        finally:
            self.ran = True
            try:
                self.on_complete()
            finally:
                self._event.set()

    def run(self, rerun=False):
        if not rerun and (self.running or self._ran):
            raise Exception('Already ran, or running this job.')

        self._event.clear()
        Callback(self._run).spawn()
