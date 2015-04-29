from ...framework.router import Component
import shlex
import datetime


class Console(Component):
    def init(self):
        self.commands = {}
        self.commands['hello'] = None
        print('Console component initialized.')

    def on_open(self, ws):
        stdin = 'astra.clients.{session_id}.stdin'.format(session_id = ws.session_id)
        stdout = 'astra.clients.{session_id}.stdout'.format(session_id = ws.session_id)
        stderr = 'astra.clients.{session_id}.stderr'.format(session_id = ws.session_id)

        def cb(message):
            if not len(message['args']):
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.publish(stderr, {}, message='Bad event format.', timestamp=timestamp)
                return

            if not len(message['args'][0]):
                return

            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.publish(stdout, {}, message=message['args'][0], timestamp=timestamp)

            self.on_command(stdout, stderr, message['args'][0])

        self.subscribe(stdin, cb)

    def on_command(self, stdout, stderr, line):
        try:
            parts = shlex.split(line, posix=True)
        except ValueError as e:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.publish(stderr, {}, message=str(e), timestamp=timestamp)
            return

        if not len(parts):
            return

        if parts[0] not in self.commands:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.publish(stderr, {}, message='No such command: ' + parts[0], timestamp=timestamp)
            return

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.publish(stdout, {}, message='Running command: ' + line, timestamp=timestamp)

    def on_close(self, ws):
        print('{0} disconnected.'.format(ws.session_id))
