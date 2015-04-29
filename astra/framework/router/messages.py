import json


__all__ = ['SubscribedMessage', 'UnsubscribedMessage', 'AbortMessage', 'WelcomeMessage',
           'PublishedMessage', 'EventMessage', 'HelloMessage', 'SubscribeMessage', 'PublishMessage']


class Message:
    _properties = None
    msg_type = None
    arguments = None

    @property
    def properties(self):
        if self._properties is None:
            self._properties = {
                'msg_type': self.msg_type
            }
        return self._properties

    def __init__(self, *args, **kwargs):
        for i in range(len(self.arguments)):
            self.properties[self.arguments[i]] = args[i]

    def __str__(self):
        return json.dumps(self.properties)

    def __getattr__(self, key):
        if key in ['properties', 'msg_type', 'arguments', '_properties']:
            return object.__getattribute__(self, key)
        elif key in self.properties:
            return self.properties[key]
        else:
            raise AttributeError(key)


class HelloMessage(Message):
    msg_type = 'hello'
    arguments = []


class SubscribeMessage(Message):
    msg_type = 'subscribe'
    arguments = ['request_id', 'options', 'topic']


class SubscribedMessage(Message):
    msg_type = 'subscribed'
    arguments = ['request_id', 'subscription_id']


class UnsubscribedMessage(Message):
    msg_type = 'unsubscribed'
    arguments = ['request_id']


class PublishMessage(Message):
    msg_type = 'publish'
    arguments = ['request_id', 'topic', 'options', 'args', 'kwargs']

class PublishedMessage(Message):
    msg_type = 'published'
    arguments = ['request_id']


class AbortMessage(Message):
    msg_type = 'abort'

    def __init__(self, reason_uri, message):
        self.properties['reason'] = reason_uri
        self.properties['details'] = {'message': message}


class WelcomeMessage(Message):
    msg_type = 'welcome'
    arguments = ['session_id', 'details']


class EventMessage(Message):
    msg_type = 'event'
    arguments = ['subscription_id', 'options', 'args', 'kwargs']

