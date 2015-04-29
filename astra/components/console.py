from ..framework.router import Component


class Console(Component):
    def init(self):
        print('Console component initialized.')

    def on_open(self, ws):
        stdin = 'astra.clients.{session_id}.stdin'.format(session_id = ws.session_id)
        stdout = 'astra.clients.{session_id}.stdout'.format(session_id = ws.session_id)
        stderr = 'astra.clients.{session_id}.stderr'.format(session_id = ws.session_id)

        def cb(message):
            print('message from {1} received: {0}'.format(message, ws.session_id))
            if not len(message['args']):
                self.publish(stderr, {}, message='You must provide an argument.')
                return

            self.publish(stdout, {}, message='Hello there, {session_id}!')

        self.subscribe(stdin, cb)

    def on_close(self, ws):
        print(ws.session_id)
