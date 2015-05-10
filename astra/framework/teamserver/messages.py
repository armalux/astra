import json
import inspect
import re
import sys


_messages = None
__all__ = ['HelloMessage', 'WelcomeMessage', 'AbortMessage', 'ErrorMessage',
           'SuccessMessage', 'PublishMessage', 'SubscribeMessage', 'UnsubscribeMessage',
           'RegisterMessage', 'UnregisterMessage', 'EventMessage', 'CallMessage',
           'InvokeMessage', 'YieldMessage', 'ExceptionMessage', 'ResultMessage']


def load():
    global _messages
    if _messages is not None:
        return _messages

    _messages = {}
    for name, value in inspect.getmembers(sys.modules[__name__]):
        if not isinstance(value, type):
            continue

        if not issubclass(value, Message):
            continue

        if value is Message:
            continue

        _messages[value.type] = value

    return _messages


class ValidatedProperty:
    def __init__(self, value_type, name, default_value=None, procedure=None, **kwargs):
        self._type = value_type
        self._procedure = procedure
        self._name = name
        self._value = default_value
        self._accepts = kwargs.get('accepts', [])

    def __get__(self, obj, cls):
        return self._value

    def __set__(self, obj, value):
        if not isinstance(value, self._type):
            raise ValueError('{0}.{1} expected type {2}, {3} found.'.format(
                obj.__class__.__name__,
                self._name,
                self._type.__name__,
                value.__class__.__name__))

        if len(self._accepts):
            for val in self._accepts:
                if val == value:
                    break
            else:
                raise ValueError('{0}.{1} accepts only {2}, not {3}'.format(
                    obj.__class__.__name__,
                    self._name,
                    ', '.join([str(x) for x in self._accepts]),
                    value))

        if self._procedure is not None:
            self._procedure(obj, value)

        self._value = value


class val:
    def __init__(self, value_type):
        self.value_type = value_type

    def __call__(self, real_procedure):
        if real_procedure.__defaults__ is not None:
            default = real_procedure.__defaults__[0]
            accepts = [default]
        else:
            default = None
            accepts = []

        return ValidatedProperty(self.value_type, real_procedure.__name__, default, real_procedure, accepts=accepts)


class MessageMeta(type):
    def __new__(meta, name, bases, dct):
        if name == 'Message':
            return type.__new__(meta, name, bases, dct)

        if '_args' not in dct:
            raise ValueError('Class {0} is missing attribute {1}.'.format(name, '_args'))

        properties = ['type']
        for key, value in dct.items():
            if isinstance(value, ValidatedProperty):
                properties.append(key)

        dct['_properties'] = properties

        type_name = ''.join(re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', name).split(' ')[:-1]).lower()

        @val(str)
        def msg_type(self, value=type_name):
            pass
        dct['type'] = msg_type

        return type.__new__(meta, name, bases, dct)

    def __call__(cls, *args, **kwargs):
        return str(type.__call__(cls, *args, **kwargs))


class Message(metaclass=MessageMeta):
    _args = []
    _properties = []

    def __init__(self, *values):
        if len(values) != len(self._args):
            raise TypeError('{0}.__init__(self, {4}) takes {1} positional argument{2} but {3} were given.'.format(
                self.__class__.__name__,
                len(self._args),
                's' if len(self._args) > 1 or len(self._args) == 0 else '',
                len(values),
                ', '.join(self._args)
                ))

        for i, name in enumerate(self._args):
            setattr(self, name, values[i])

    @classmethod
    def from_dict(cls, data):
        args = [data[cls._args[i]] for i in range(len(cls._args))]
        return cls.instance(*args)

    @classmethod
    def instance(cls, *args):
        obj = object.__new__(cls, *args)
        obj.__init__(*args)
        return obj

    def __str__(self):
        data = {name: getattr(self, name) for name in self._properties}
        return json.dumps(data)


class HelloMessage(Message):
    _args = []


class WelcomeMessage(Message):
    _args = ['session_id']

    @val(int)
    def session_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')


class AbortMessage(Message):
    _args = ['reason_uri', 'message']

    @val(str)
    def reason_uri(self, value):
        pass

    @val(str)
    def message(self, value):
        pass


class ErrorMessage(Message):
    _args = ['request_id', 'message']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def message(self, value):
        pass


class SuccessMessage(Message):
    _args = ['request_id']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')


class PublishMessage(Message):
    _args = ['request_id', 'topic', 'args', 'kwargs']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def topic(self, value):
        pass

    @val(list)
    def args(self, value):
        pass

    @val(dict)
    def kwargs(self, value):
        pass


class SubscribeMessage(Message):
    _args = ['request_id', 'topic']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def topic(self, value):
        pass


class UnsubscribeMessage(Message):
    _args = ['request_id', 'topic']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def topic(self, value):
        pass


class RegisterMessage(Message):
    _args = ['request_id', 'procedure']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def procedure(self, value):
        pass


class UnregisterMessage(Message):
    _args = ['request_id', 'procedure']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def procedure(self, value):
        pass


class EventMessage(Message):
    _args = ['topic', 'args', 'kwargs']

    @val(str)
    def topic(self, value):
        pass

    @val(list)
    def args(self, value):
        pass

    @val(dict)
    def kwargs(self, value):
        pass


class CallMessage(Message):
    _args = ['request_id', 'procedure', 'args', 'kwargs']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def procedure(self, value):
        pass

    @val(list)
    def args(self, value):
        pass

    @val(dict)
    def kwargs(self, value):
        pass


class InvokeMessage(Message):
    _args = ['invoke_id', 'procedure', 'args', 'kwargs']

    @val(int)
    def invoke_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def procedure(self, value):
        pass

    @val(list)
    def args(self, value):
        pass

    @val(dict)
    def kwargs(self, value):
        pass


class YieldMessage(Message):
    _args = ['invoke_id', 'result']

    @val(int)
    def invoke_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(dict)
    def result(self, value):
        pass


class ExceptionMessage(Message):
    _args = ['invoke_id', 'message']

    @val(int)
    def invoke_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(str)
    def message(self, value):
        pass


class ResultMessage(Message):
    _args = ['request_id', 'result']

    @val(int)
    def request_id(self, value):
        if value > 9007199254740992 or value < 0:
            raise ValueError('session_id out of range.')

    @val(dict)
    def result(self, value):
        pass



