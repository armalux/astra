from tornado.websocket import WebSocketHandler, websocket_connect
from tornado import gen
from tornado.ioloop import IOLoop
import json
import random
from .messages import *
from ..service import ServiceUser


class AstraClient:
    _messages = None
    session_id = None

    def __init__(self, url):
        self._initialize()
        IOLoop.current().add_callback(self._connect, url)

    @gen.coroutine
    def _connect(self, url):
        self._ws = yield websocket_connect(url, on_message_callback=self._on_message)
        self._on_open()

    @property
    def next_request_id(self):
        return next(self._next_request_id)

    def init(self):
        pass

    @property
    def messages(self):
        if self.__class__._messages is None:
            from . import messages
            self.__class__._messages = {}
            for name, value in inspect.getmembers(messages):
                if not isinstance(value, type):
                    continue

                if not issubclass(value, messages.Message):
                    continue

                if value is messages.Message:
                    continue

                self.__class__._messages[value.type] = value

        return self.__class__._messages

    def _on_message(self, msg):
        if msg is None:
            return

        try:
            msg = json.loads(msg)
        except ValueError:
            return

        if 'type' not in msg:
            return

        if msg['type'] not in self.messages:
            return

        msg = self.messages[msg['type']].from_dict(msg)

        if msg.type == 'welcome':
            self.session_id = msg.session_id
            self.init()

        elif msg.type == 'invoke':
            if msg.procedure not in self._procedures:
                return

            result = self._procedures[msg.procedure](*msg.args, **msg.kwargs)
            if result is None:
                result = {}

            self._ws.write_message(YieldMessage(msg.invoke_id, result))

        elif msg.type == 'event':
            if msg.topic not in self._subscriptions:
                return

            for handler in self._subscriptions[msg.topic]:
                handler(*msg.args, **msg.kwargs)

        elif msg.type == 'success':
            if msg.request_id not in self._pending_requests:
                return

            del self._pending_requests[msg.request_id]

        elif msg.type == 'error':
            if msg.request_id not in self._pending_requests:
                return

            del self._pending_requests[msg.request_id]

    def subscribe(self, topic, callback):
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
            msg = SubscribeMessage.instance(self.next_request_id, topic)
            self._pending_requests[msg.request_id] = msg
            self._ws.write_message(str(msg))

        self._subscriptions[topic].append(callback)

    def register(self, procedure, callback):
        if procedure in self._procedures:
            raise ValueError('Procedure "{0}" is already registered.'.format(procedure))

        self._procedures[procedure] = callback
        msg = RegisterMessage.instance(self.next_request_id, procedure)
        self._pending_requests[msg.request_id] = msg
        self._ws.write_message(str(msg))

    def publish(self, topic, *args, **kwargs):
        msg = PublishMessage.instance(self.next_request_id, topic, list(args), kwargs)
        self._pending_requests[msg.request_id] = msg
        self._ws.write_message(str(msg))

    def call(self, callback, procedure, *args, **kwargs):
        msg = CallMessage.instance(self.next_request_id, procedure, list(args), kwargs)
        self._pending_requests[msg.request_id] = msg
        self._pending_calls[msg.request_id] = callback
        self._ws.write_message(str(msg))

    def _initialize(self):
        self.session_id = None
        self._subscriptions = {}
        self._procedures = {}
        self._pending_requests = {}
        self._pending_calls = {}
        self._next_request_id = iter(range(0, 9007199254740992))

    def _on_open(self):
        self._ws.write_message(HelloMessage())


class Component(AstraClient, ServiceUser):
    def init(self):
        pass

    def on_client_connect(self, session_id):
        pass

    def on_client_disconnect(self, session_id):
        pass

    def on_client_subscribe(self, session_id, topic):
        pass

    def on_client_unsubscribe(self, session_id, topic):
        pass

    def on_client_register(self, session_id, procedure):
        pass

    def on_client_unregister(self, session_id, procedure):
        pass

    def on_client_call(self, session_id, procedure, *args, **kwargs):
        pass

    def on_client_publish(self, session_id, topic, *args, **kwargs):
        pass


import shlex
import datetime
class ConsoleComponent(Component):
    def init(self):
        self.commands = {}
        self.commands['hello'] = None
        self.register('astra.teamserver.commands.run', self.on_command)

    def on_command(self, cmd):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not len(cmd):
            return

        try:
            parts = shlex.split(cmd, posix=True)
        except ValueError as e:
            return { 'pipe': 'stderr', 'message': str(e), 'timestamp': timestamp }

        if not len(parts):
            return

        if parts[0] not in self.commands:
            return { 'pipe': 'stderr', 'message': 'No such command "{0}"'.format(parts[0]), 'timestamp': timestamp }

        return {'pipe': 'stdout', 'message': 'Running command...', 'timestamp': timestamp }


class TeamServerHandler(WebSocketHandler):
    _invocations = {}
    _subscriptions = {}
    _procedures = {}
    _sessions = {}
    _components = None
    _messages = None
    session_id = None
    _next_invoke_id = iter(range(0, 9007199254740992))

    @property
    def new_session_id(self):
        while True:
            session_id = random.SystemRandom().randint(0,9007199254740992)
            if session_id not in self.sessions:
                break

        return session_id

    @property
    def next_invoke_id(self):
        return next(self.__class__._next_invoke_id)

    @property
    def invocations(self):
        return self.__class__._invocations

    @property
    def subscriptions(self):
        return self.__class__._subscriptions

    @property
    def procedures(self):
        return self.__class__._procedures

    @property
    def sessions(self):
        return self.__class__._sessions

    @property
    def messages(self):
        if self.__class__._messages is None:
            from . import messages
            self.__class__._messages = {}
            for name, value in inspect.getmembers(messages):
                if not isinstance(value, type):
                    continue

                if not issubclass(value, messages.Message):
                    continue

                if value is messages.Message:
                    continue

                self.__class__._messages[value.type] = value

        return self.__class__._messages

    @property
    def components(self):
        if self.__class__._components is None:
            cls.load_components()

        return self.__class__._components

    @classmethod
    def load_components(cls):
        cls._components = []
        cls._components.append(ConsoleComponent('ws://127.0.0.1:8080/ws'))

    def on_close(self):
        if self.session_id is None:
            return

        if self.request.remote_ip != '127.0.0.1':
            for comp in self.components:
                comp.on_client_disconnect(self.session_id)

        del self.sessions[self.session_id]

        for topic, subs in self.subscriptions.items():
            if self.session_id in subs:
                subs.remove(self.session_id)

        procedures_to_delete = []
        for procedure, session_id in self.procedures.items():
            if self.session_id == session_id:
                procedures_to_delete.append(procedure)

        for procedure in procedures_to_delete:
            del self.procedures[procedure]

        invocations_to_delete = []
        for invoke_id, details in self.invocations.items():
            if self.session_id == details['session_id']:
                invocations_to_delete.append(invoke_id)

        for invocation in invocations_to_delete:
            del self.invocations[invocation]


    def on_message(self, msg):
        try:
            msg = json.loads(msg)
        except ValueError:
            self.close()
            return

        if 'type' not in msg or msg['type'] not in self.messages:
            self.close()
            return

        msg = self.messages[msg['type']].from_dict(msg)

        if msg.type != 'hello' and self.session_id is None:
            self.close()
            return

        if msg.type == 'hello' and self.session_id is not None:
            self.close()
            return

        if msg.type == 'hello':
            session_id = self.new_session_id
            self.sessions[session_id] = self
            self.session_id = session_id
            if self.request.remote_ip != '127.0.0.1':
                for comp in self.components:
                    comp.on_client_connect(session_id)
            self.write_message(WelcomeMessage(session_id))

        elif msg.type == 'subscribe':
            if msg.topic not in self.subscriptions:
                self.subscriptions[msg.topic] = set()

            if self.session_id in self.subscriptions[msg.topic]:
                self.write_message(ErrorMessage(msg.request_id, 'Already subscribed.'))
                return

            if self.request.remote_ip != '127.0.0.1':
                for comp in self.components:
                    if comp.on_client_subscribe(self.session_id, msg.topic) is False:
                        return

            self.subscriptions[msg.topic].add(self.session_id)
            self.write_message(SuccessMessage(msg.request_id))

        elif msg.type == 'unsubscribe':
            if msg.topic not in self.subscriptions:
                self.write_message(ErrorMessage(msg.request_id, 'Not subscribed to this topic.'))
                return

            if msg.request_id not in self.subscriptions[msg.topic]:
                self.write_message(ErrorMessage(msg.request_id, 'Not subscribed to this topic.'))
                return

            if self.request.remote_ip != '127.0.0.1':
                for comp in self.components:
                    if comp.on_client_unsubscribe(self.session_id, msg.topic) is False:
                        return

            self.subscriptions[msg.topic].remove(self.session_id)
            self.write_message(SuccessMessage(msg.request_id))

        elif msg.type == 'publish':
            if msg.topic not in self.subscriptions:
                self.write_message(SuccessMessage(msg.request_id))
                return

            if self.request.remote_ip != '127.0.0.1':
                for comp in self.components:
                    if comp.on_client_publish(self.session_id, msg.topic, *msg.args, **msg.kwargs) is False:
                        return

            event = EventMessage(msg.topic, msg.args, msg.kwargs)
            for session_id in self.subscriptions[msg.topic]:
                self.sessions[session_id].write_message(event)

            self.write_message(SuccessMessage(msg.request_id))

        elif msg.type == 'call':
            if msg.procedure not in self.procedures:
                self.write_message(ErrorMessage(msg.request_id, 'Proceedure does not exist.'))
                return

            if self.request.remote_ip != '127.0.0.1':
                for comp in self.components:
                    if comp.on_client_call(self.session_id, msg.procedure, *msg.args, **msg.kwargs) is False:
                        return

            invoke_id = self.next_invoke_id
            self.invocations[invoke_id] = { 'session_id': self.session_id, 'request_id': msg.request_id }
            self.sessions[self.procedures[msg.procedure]].write_message(InvokeMessage(invoke_id, msg.procedure, msg.args, msg.kwargs))

        elif msg.type == 'register':
            if msg.procedure in self.procedures:
                self.write_message(ErrorMessage(msg.request_id, 'Procedure already registered.'))
                return

            if self.request.remote_ip != '127.0.0.1':
                for comp in self.components:
                    if comp.on_client_register(self.session_id, msg.procedure) is False:
                        return

            self.procedures[msg.procedure] = self.session_id
            self.write_message(SuccessMessage(msg.request_id))

        elif msg.type == 'unregister':
            if msg.procedure not in self.procedures:
                pass

            if self.procedures[msg.procedure] != self.session_id:
                self.write_message(ErrorMessage(msg.request_id, 'Procedure not registered to you.'))

            if self.request.remote_ip != '127.0.0.1':
                for comp in self.components:
                    if comp.on_client_unregister(self.session_id, msg.procedure) is False:
                        return

            del self.procedures[msg.procedure]

        elif msg.type == 'exception':
            if msg.invoke_id not in self.invocations:
                return

            session_id = self.invocations[msg.invoke_id]['session_id']
            request_id = self.invocations[msg.invoke_id]['request_id']

            self.sessions[session_id].write_message(ErrorMessage(request_id, msg.message))

        elif msg.type == 'yield':
            if msg.invoke_id not in self.invocations:
                return

            session_id = self.invocations[msg.invoke_id]['session_id']
            request_id = self.invocations[msg.invoke_id]['request_id']

            self.sessions[session_id].write_message(ResultMessage(request_id, msg.result))

        else:
            self.close()
            return

