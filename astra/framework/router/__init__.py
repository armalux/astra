import json
from tornado.websocket import WebSocketHandler
from sqlalchemy import create_engine
from ..service import ServiceUser
from ..singleton import Singleton
from .database import Session, Peer, Subscription
from .validation import *
from .messages import *


__all__ = ['MessageHandler', 'ClientSession', 'Router', 'validation', 'messages']


class MessageHandler(ServiceUser, WebSocketHandler):
    session_id = None

    def on_close(self):
        if self.session_id is not None:
            self.services.router.remove_session(self.session_id)

    def write_message(self, message):
        print(message)
        super().write_message(message)

    def on_message(self, message):
        print(message)
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
        self.database = Session()
        self._websockets = {}

    def create_session(self, ws):
        peer = Peer(session_id = self.new_session_id)
        self.database.add(peer)
        self.database.flush()
        ws.session_id = peer.session_id
        self._websockets[peer.session_id] = ws

    def remove_session(self, session_id):
        self.database.query(Peer).filter(Peer.session_id == session_id).delete()
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

        subscriptions = self.database.query(Subscription).filter(Subscription.topic == data.topic)
        for subscription in subscriptions:
            msg = EventMessage(subscription.id, data.options, data.args, data.kwargs)
            ws.write_message(str(msg))

    def handle_unsubscribe(self, session, data):
        pass

