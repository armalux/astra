from ...framework.router import Component
import shlex

class Console(Component):
    def init(self):
        print('Console component initialized.')
        self.commands = {}
        self.commands['hello'] = []

    def on_open(self, ws):
        stdin = 'astra.clients.{session_id}.stdin'.format(session_id = ws.session_id)
        stdout = 'astra.clients.{session_id}.stdout'.format(session_id = ws.session_id)
        stderr = 'astra.clients.{session_id}.stderr'.format(session_id = ws.session_id)

        def cb(message):
            if not len(message['args']):
                self.publish(stderr, {}, message='Bad event format.')
                return

            self.on_command(stdout, stderr, message['args'][0])

        self.subscribe(stdin, cb)

    def on_command(self, stdout, stderr, line):
        parts = shlex.split(line, posix=True)
        if not len(parts):
            return

        if parts[0] not in self.commands:
            self.publish(stderr, {}, message='No such command: ' + parts[0])
            return

        self.publish(stdout, {}, message='Running command: ' + line)

    def on_close(self, ws):
        print(ws.session_id)
