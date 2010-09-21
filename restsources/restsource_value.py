# -*- coding: utf8 -*-

from datetime import datetime, date

__all__ = ('RestsourceValue', 'Unicode', 'Bytes',
           'Integer', 'Float',
           'Date', 'Datetime',
           'Object', 'ObjectCollection')


class RestsourceValue(object):
    def __repr__(self):
        return u"<%s: %s>" % (self.__class__.__name__, repr(self.value))

    value = property(lambda self: self._value)

    @classmethod
    def get_for_value(cls, value):
        simple_types_map = {
            unicode: Unicode,
            str: Bytes,
            int: Integer,
            long: Integer,
            float: Float,
            date: Date,
            datetime: Datetime,
        }
        try:
            return simple_types_map[type(value)](value)
        except KeyError:
            raise TypeError(type(value))


class Unicode(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, unicode)
        self._value = value

class Bytes(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, str)
        self._value = value

class Integer(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, (int, long))
        self._value = value

class Float(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, float)
        self._value = value

class Date(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, date)
        self._value = value

class Datetime(RestsourceValue):
    def __init__(self, value):
        assert isinstance(value, datetime)
        self._value = value




class Object(RestsourceValue):
    def __init__(self, name, data, primary_fields=()):
        assert isinstance(name, (unicode, str))
        assert isinstance(data, dict)
        assert all(isinstance(k, RestsourceValue) and (isinstance(v, RestsourceValue) or v is None) for (k,v) in data.items())
        assert isinstance(primary_fields, (list, tuple, set))
        assert all(isinstance(x, (unicode, str)) for x in primary_fields)
        assert all(x in (y.value for y in data) for x in primary_fields)
        self._value = {
            'name': name,
            'data': data,
            'primary_fields': tuple(primary_fields) }

    @classmethod
    def from_dict(cls, name, dic):
        rvdata = {}
        for k,v in dic.iteritems():
            rvdata[RestsourceValue.get_for_value(k)] = RestsourceValue.get_for_value(v)
        return cls(name, rvdata)


class ObjectCollection(RestsourceValue):
    def __init__(self, name, collection):
        assert isinstance(name, (unicode, str))
        assert all(isinstance(x, Object) for x in collection)
        self._value = {
            'name': name,
            'collection': collection }

