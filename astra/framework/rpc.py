from tornado import websocket
import json


class ValidationException(Exception):
    pass


def validated_property(prop_type):
    def function_generator(real_function):
        def getter(self):
            return getattr(self, '_' + real_function.__name__)

        def setter(self, value):
            if not isinstance(value, prop_type):
                raise ValidationException(real_function.__name__)

            real_function(self, value)
            setattr(self, '_' + real_function.__name__, value)

        return property(getter, setter)

    return function_generator


class Handler:
    _msg_type = None
    __properties__ = []

    @validated_property(str)
    def msg_type(self, value):
        if value != self._msg_type:
            raise ValidationException('msg_type != {0}'.format(self._msg_type))

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        for attr_name, attr_value in cls.__dict__.items():
            if not isinstance(attr_value, property):
                continue

            obj.__properties__.append(attr_name)
            setattr(obj, '_' + attr_name, None)

        return obj

    def __init__(self, data):
        for prop_name in self.__properties__:
            if prop_name not in data:
                raise ValidationException('Missing {0}.'.format(prop_name))
            setattr(self, prop_name, data[prop_name])

    def handle(self, ws):
        raise NotImplementedError()


class SubscribeHandler(Handler):
    _msg_type = 'subscribe'

    @validated_property(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValidationException('Request ID out of range.')

    @validated_property(dict)
    def options(self, value):
        pass

    @validated_property(str)
    def topic(self, value):
        pass


class HelloHandler(ServiceUser, Handler):
    _msg_type = 'hello'

    @validated_property(str)
    def realm(self, value):
        pass

    @validated_property(dict)
    def details(self, value):
        pass

    def handle(self, ws):
        if self.realm not in ws._realms:
            ws.close()
            return

        session_id = self.services.random.integer(0, 9007199254740992)


class MessageHandler(websocket.WebSocketHandler):
    _handlers = {
        'hello': HelloHandler,
        'subscribe': SubscribeHandler
    }

    _realms = {
        'astra.realm': {
        }
    }

    _sessions = {}

    def on_message(self, message):
        try:
            message = json.loads(message)
        except ValueError:
            self.close()
            return

        if 'msg_type' not in message:
            self.close()
            return

        if message['msg_type'] not in self._handlers:
            self.close()
            return

        try:
            handler = self._handlers[message['msg_type']](message)
        except ValidationException:
            self.close()
            return

        handler.handle(self)




