from tornado import websocket
import json


class JsonMessage:
    __properties__ = {}

    def __new__(cls, data):
        obj = object.__new__(cls)
        for name, value_type in cls.__properties__.items():
            if name not in data:
                raise ValueError(name)

            try:
                value = value_type(data[name])
            except ValueError:
                raise ValueError('Bad type: {0}'.format(name))

            setattr(obj, name, value)

        return obj

    def process(self, message):
        raise NotImplementedError()


class SubscribeMessage(JsonMessage):
    __type__ = 'subscribe'
    __properties__ = {
        'channel': str
    }


class PublishMessage(JsonMessage):
    __type__ = 'publish'
    __properties__ = {
        'channel': str,
        'message': str
    }


class MessageHandler(websocket.WebSocketHandler):
    channels = {}

    def publish(self, channel, message):
        if channel not in self.channels:
            self.channels[channel] = []
            return

        msg = json.dumps({
            'type': 'publish',
            'channel': channel,
            'message': message
        })

        for subscriber in self.channels[channel]:
            subscriber.write_message(msg)

    def subscribe(self, channel):
        if channel not in self.channels:
            self.channels[channel] = []

        if self not in self.channels[channel]:
            self.channels[channel].append(self)

    def on_close(self):
        for channel, subscribers in self.channels.items():
            if self in subscribers:
                subscribers.remove(self)

    def on_message(self, message):
        try:
            message = json.loads(message)
        except ValueError:
            self.close()
            return

        if 'type' not in message:
            self.close()
            return

        if message['type'] == 'subscribe':
            message = SubscribeMessage(message)
            self.subscribe(message.channel)

        elif message['type'] == 'publish':
            message = PublishMessage(message)
            self.publish(message.channel, message.message)

        else:
            self.close()
            return

