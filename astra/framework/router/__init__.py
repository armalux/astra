import json
from tornado.websocket import WebSocketHandler, websocket_connect
from tornado.ioloop import IOLoop
from tornado import gen
from importlib import import_module
from sqlalchemy import create_engine
from ..service import ServiceUser
from ..singleton import Singleton
from .database import Session, Peer, Subscription
from .validation import *
from .messages import *


__all__ = ['MessageHandler', 'ClientSession', 'Router', 'Component', 'validation', 'messages']


class Component(ServiceUser):
    def __init__(self):
        self._next_request_id = iter(range(0,9007199254740992));
        self._subscriptions = {}
        self._event_handlers = {}
        self._pending_requests = {}

        @gen.coroutine
        def connect(self):
            self._conn = yield websocket_connect('ws://127.0.0.1:8080/ws',
                IOLoop.instance(),
                on_message_callback=self._on_message)
            self._on_open()

        IOLoop.instance().spawn_callback(connect, self)

    @property
    def next_request_id(self):
        return next(self._next_request_id)

    def _on_welcome(self):
        pass

    def _on_message(self, message):
        if message is None:
            self._conn.close()
            return
        message = json.loads(message)

        if message['msg_type'] == 'welcome':
            self.session_id = message['session_id']
            self.init()

        elif message['msg_type'] == 'subscribed':
            request = self._pending_requests[message['request_id']]
            del self._pending_requests[message['request_id']]
            self._subscriptions[message['subscription_id']] = request.topic

        elif message['msg_type'] == 'event':
            topic = self._subscriptions[message['subscription_id']]

            if topic not in self._event_handlers:
                raise Exception('Unhandled event subscription.')

            for callback in self._event_handlers[topic]:
                callback(message)

    def _on_open(self):
        self._conn.write_message(str(HelloMessage()))

    def subscribe(self, topic, callback):
        request = SubscribeMessage(self.next_request_id, {}, topic)

        if topic not in self._event_handlers:
            self._event_handlers[topic] = []
        self._event_handlers[topic].append(callback)

        self._pending_requests[request.request_id] = request
        self._conn.write_message(str(request))

    def publish(self, topic, options={}, *args, **kwargs):
        request = PublishMessage(self.next_request_id, topic, options, args, kwargs)
        self._conn.write_message(str(request))

    def init(self):
        pass

    def on_open(self, ws):
        pass

    def on_close(self, ws):
        pass


class MessageHandler(ServiceUser, WebSocketHandler):
    session_id = None

    def on_close(self):
        if self.session_id is not None:
            self.services.router.remove_session(self.session_id)

    def write_message(self, message):
        super().write_message(message)

    def on_message(self, message):
        try:
            message = json.loads(message)
        except ValueError:
            self.close()
            return

        if message is None:
            self.close()
            return

        if 'msg_type' not in message:
            self.close()
            return

        self.services.router.route(self, message)


class Router(Singleton, ServiceUser):
    def __init__(self):
        self.database = Session()
        self._websockets = {}
        self._components_initialized = False
        self._component_session_ids = []

    def load_components(self):
        self.components = []
        for comp in import_module('...components', __name__).components:
            obj = comp()
            self.components.append(obj)

    @property
    def components_initialized(self):
        if self._components_initialized == False:
            for comp in self.components:
                if not hasattr(comp, 'session_id'):
                    break
            else:
                self._components_initialized = True

        return self._components_initialized

    def create_session(self, ws):
        peer = Peer(session_id = self.new_session_id)
        self.database.add(peer)
        self.database.flush()
        ws.session_id = peer.session_id
        self._websockets[peer.session_id] = ws

        if not self.components_initialized:
            self._component_session_ids.append(peer.session_id)
            return

        for comp in self.components:
            comp.on_open(ws)

    def remove_session(self, session_id):
        if not session_id in self._component_session_ids:
            for comp in self.components:
                comp.on_close(self._websockets[session_id])

        peer = self.database.query(Peer).filter(Peer.session_id == session_id).first()
        self.database.query(Subscription).filter(Subscription.peer_id == peer.id).delete()
        self.database.query(Peer).filter(Peer.session_id == session_id).delete()
        self.database.commit()
        del self._websockets[session_id]

    @property
    def new_session_id(self):
        session_ids = [x.session_id for x in self.database.query(Peer).all()]
        minimum = 0
        maximum = 9007199254740992 # 2^53
        session_id = self.services.random.integer(minimum, maximum)
        while session_id in session_ids:
            session_id = self.services.random.integer(minimum, maximum)
        return session_id

    def route(self, ws, data):
        handler = getattr(self, 'handle_' + data['msg_type'])

        if data['msg_type'] == 'hello':
            handler(ws, data)
        else:
            if ws.session_id is None:
                ws.close()
                return
            handler(ws, data)

        self.database.commit()

    def handle_hello(self, ws, data):
        data = HelloValidator(data)

        if ws.session_id is not None:
            msg = AbortMessage('astra.error.session_already_established', 'Session already established.')
            ws.write_message(str(msg))
            return

        self.create_session(ws)

        msg = WelcomeMessage(ws.session_id, {})
        ws.write_message(str(msg))

    def handle_subscribe(self, ws, data):
        data = SubscribeValidator(data)

        peer = self.database.query(Peer).filter(Peer.session_id == ws.session_id).first()
        subscription = Subscription(topic=data.topic, peer_id=peer.id)
        self.database.add(subscription)
        self.database.flush()

        msg = SubscribedMessage(data.request_id, subscription.id)
        ws.write_message(str(msg))

    def handle_publish(self, ws, data):
        data = PublishValidator(data)
        msg = PublishedMessage(data.request_id)
        ws.write_message(str(msg))

        for subscription in self.database.query(Subscription).filter(Subscription.topic == data.topic):
            msg = EventMessage(subscription.id, data.options, data.args, data.kwargs)
            self._websockets[subscription.peer.session_id].write_message(str(msg))

    def handle_unsubscribe(self, session, data):
        pass

