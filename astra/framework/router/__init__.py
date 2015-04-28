import json
from tornado.websocket import WebSocketHandler
from ..service import ServiceUser
from ..singleton import Singleton
from .validation import *
from .messages import *


__all__ = ['MessageHandler', 'ClientSession', 'Router', 'validation', 'messages']


class ClientSession:
    def __init__(self, router, ws, realm, roles):
        self.router = router
        self.ws = ws
        self.id = router.new_session_id
        self.roles = roles
        self.realm = realm

        ws.session = self
        router._sessions[self.id] = self

    def on_close(self):
        del self.router._sessions[self.id]

    def send_welcome(self):
        msg = WelcomeMessage(self.id, {'roles': { 'dealer': {}, 'broker': {}}})
        self.ws.write_message(str(msg))


class MessageHandler(ServiceUser, WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = None

    def on_close(self):
        if self.session is not None:
            self.session.on_close()

    def on_message(self, message):
        try:
            message = json.loads(message)
        except ValueError:
            self.close()
            return

        if 'msg_type' not in message:
            self.close()
            return

        self.services.router.route(self, message)


class Router(Singleton, ServiceUser):
    def __init__(self):
        self._handlers = {}
        self._realms = { 'astra': {} }
        self._sessions = {}

    @property
    def new_session_id(self):
        minimum = 0
        maximum = 9007199254740992 # 2^53
        session_id = self.services.random.integer(minimum, maximum)
        while session_id in self._sessions:
            session_id = self.services.random.integer(minimum, maximum)
        return session_id

    def route(self, ws, data):
        handler = getattr(self, 'handle_' + data['msg_type'])
        if data['msg_type'] == 'hello':
            handler(ws, data)
        else:
            if ws.session is None:
                ws.close()
                return
            handler(ws.session, data)

    def handle_hello(self, ws, data):
        data = HelloValidator(data)

        if ws.session is not None:
            msg = AbortMessage('astra.error.session_already_established', 'Session already established.')
            ws.write_message(str(msg))
            return

        if data.realm not in self._realms:
            msg = AbortMessage('astra.error.no_such_realm', 'No such realm "{0}".'.format(data.realm))
            ws.write_message(str(msg))
            return

        session = ClientSession(self, ws, data.realm, list(data.details['roles']))
        session.send_welcome()

    def handle_subscribe(self, session, data):
        data = SubscribeValidator(data)


    def handle_unsubscribe(self, session, data):
        pass

