# -*- coding: utf8 -*-

__all__ = ('RestsourceValue', 'RestsourceValueUnicode', 'RestsourceValueBytes',
           'RestsourceValueInteger', 'RestsourceValueFloat',
           'RestsourceValueObject', 'RestsourceValueObjectCollection')


class RestsourceValue(object):
    def __repr__(self):
        return u"<%s: %s>" % (self.__class__.__name__, repr(self.value))

    value = property(lambda self: self._value)

    @classmethod
    def get_for_value(cls, value):
        simple_types_map = {
            unicode: RestsourceValueUnicode,
            str: RestsourceValueBytes,
            int: RestsourceValueInteger,
            long: RestsourceValueInteger,
            float: RestsourceValueFloat,
        }
        try:
            return simple_types_map[type(value)](value)
        except KeyError:
            raise TypeError(type(value))

class RestsourceValueUnicode(unicode, RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, unicode)
        self._value = value

class RestsourceValueBytes(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, str)
        self._value = value

class RestsourceValueInteger(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, (int, long))
        self._value = value

class RestsourceValueFloat(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, float)
        self._value = value


class RestsourceValueObject(RestsourceValue):
    def __init__(self, name, data, attributes=()):
        assert isinstance(name, (unicode, str))
        assert isinstance(data, dict)
        assert all(isinstance(k, RestsourceValue) and isinstance(v, RestsourceValue) for (k,v) in data.items())
        assert isinstance(attributes, (list, tuple, set))
        assert all(isinstance(x, (unicode, str)) for x in attributes)
        self._value = {
            'name': name,
            'data': data,
            'attributes': tuple(attributes) }

class RestsourceValueObjectCollection(RestsourceValue):
    def __init__(self, name, collection):
        assert isinstance(name, (unicode, str))
        assert all(isinstance(x, RestsourceValueObject) for x in collection)
        self._value = {
            'name': name,
            'collection': collection }


