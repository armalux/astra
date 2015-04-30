from tornado.websocket import WebSocketHandler, websocket_connect
import json
import random
from ...components import load as load_components
from .messages import load as load_messages
from .messages import *


class TeamServerHandler(WebSocketHandler):
    _invocations = {}
    _subscriptions = {}
    _procedures = {}
    _sessions = {}
    _components = None
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
        return load_messages()

    @property
    def components(self):
        if self.__class__._components is None:
            self.__class__.load_components()

        return self.__class__._components

    @classmethod
    def load_components(cls):
        cls._components = []
        for comp in load_components():
            cls._components.append(comp('ws://127.0.0.1:8080/ws'))

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

