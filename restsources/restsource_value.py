# -*- coding: utf8 -*-

from datetime import datetime, date

__all__ = ('RestsourceValue', 'RestsourceValueUnicode', 'RestsourceValueBytes',
           'RestsourceValueInteger', 'RestsourceValueFloat',
           'RestsourceValueDate', 'RestsourceValueDatetime',
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
            date: RestsourceValueDate,
            datetime: RestsourceValueDatetime,
        }
        try:
            return simple_types_map[type(value)](value)
        except KeyError:
            raise TypeError(type(value))

class RestsourceValueUnicode(RestsourceValue):
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

class RestsourceValueDate(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, date)
        self._value = value

class RestsourceValueDatetime(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, datetime)
        self._value = value




class RestsourceValueObject(RestsourceValue):
    def __init__(self, name, data, primary_fields=()):
        assert isinstance(name, (unicode, str))
        assert isinstance(data, dict)
        assert all(isinstance(k, RestsourceValue) and isinstance(v, RestsourceValue) for (k,v) in data.items())
        assert isinstance(primary_fields, (list, tuple, set))
        assert all(isinstance(x, (unicode, str)) for x in primary_fields)
        assert all(x in (y.value for y in data) for x in primary_fields)
        self._value = {
            'name': name,
            'data': data,
            'primary_fields': tuple(primary_fields) }

class RestsourceValueObjectCollection(RestsourceValue):
    def __init__(self, name, collection):
        assert isinstance(name, (unicode, str))
        assert all(isinstance(x, RestsourceValueObject) for x in collection)
        self._value = {
            'name': name,
            'collection': collection }


