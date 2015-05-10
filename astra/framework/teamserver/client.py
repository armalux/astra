from tornado import gen
from tornado.ioloop import IOLoop
from tornado.websocket import websocket_connect
import json
from threading import Event
from . import messages


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
        return messages.load()

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

            self._ws.write_message(messages.YieldMessage(msg.invoke_id, result))

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
            msg = messages.SubscribeMessage.instance(self.next_request_id, topic)
            self._pending_requests[msg.request_id] = msg
            self._ws.write_message(str(msg))

        self._subscriptions[topic].append(callback)

    def register(self, procedure, callback):
        if procedure in self._procedures:
            raise ValueError('Procedure "{0}" is already registered.'.format(procedure))

        self._procedures[procedure] = callback
        msg = messages.RegisterMessage.instance(self.next_request_id, procedure)
        self._pending_requests[msg.request_id] = msg
        self._ws.write_message(str(msg))

    def publish(self, topic, *args, **kwargs):
        msg = messages.PublishMessage.instance(self.next_request_id, topic, list(args), kwargs)
        self._pending_requests[msg.request_id] = msg
        self._ws.write_message(str(msg))

    def call(self, callback, procedure, *args, **kwargs):
        msg = messages.CallMessage.instance(self.next_request_id, procedure, list(args), kwargs)
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
        self._ws.write_message(messages.HelloMessage())

    def blocking_call(self, procedure, *args, **kwargs):
        result = None
        event = Event()

        def callback(details):
            result = details
            event.set()

        self.call(callback, procedure, *args, **kwargs)
        event.wait()
        return result


