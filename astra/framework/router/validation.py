__all__ = ['ValidationException', 'SubscribeValidator', 'HelloValidator', 'PublishValidator']


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


class Validator:
    _msg_type = None
    __properties__ = None

    @validated_property(str)
    def msg_type(self, value):
        if value != self._msg_type:
            raise ValidationException('msg_type != {0}'.format(self._msg_type))

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj.__properties__ = []

        for attr_name, attr_value in cls.__dict__.items():
            if not isinstance(attr_value, property):
                continue

            obj.__properties__.append(attr_name)
            setattr(obj, '_' + attr_name, None)

        return obj

    def __init__(self, data):
        self.msg_type = data['msg_type']
        for prop_name in self.__properties__:
            if prop_name not in data:
                raise ValidationException('Missing {0}.'.format(prop_name))
            setattr(self, prop_name, data[prop_name])


class SubscribeValidator(Validator):
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


class PublishValidator(Validator):
    _msg_type = 'publish'

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

    @validated_property(list)
    def args(self, value):
        pass

    @validated_property(dict)
    def kwargs(self, value):
        pass


class HelloValidator(Validator):
    _msg_type = 'hello'

