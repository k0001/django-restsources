# -*- coding: utf8 -*-
import types
from datetime import date, datetime


__all__ = 'RObjectList', 'RObject',


class RObjectList(list):
    """A list of RObject objects"""

    def __init__(self, name=None, *robjects):
        """
            name : unicode | None
                Name for this RObject (if any)

            robjects : RObject list
                RObject list
        """
        self.name = name
        super(RObjectList, self).__init__(*robjects)


class RObject(object):
    """
    Python's dict-like enforcing key and value types.

    Configurable attributes::

    key_types : tuple
        Allowed key types.

    value_types_simple : tuple
        Allowed value types (simple, no nested objects nor collections)

    value_types_nested_collection : tuple
        Allowed value types for nested collections of RObjects.

    allow_nested_single : bool
        Allow nested RObject as values too.

    Trivia: It's called "RObject" because naming things suck and I couldn't come up with anything better.
    """
    key_types = unicode,
    value_types_simple = unicode, str, int, long, float, date, datetime, types.NoneType
    value_types_nested_collection = RObjectList,
    allow_nested_single = True
    special_keys = ()

    def __init__(self, name=None, dic=None, special_keys=()):
        """
            name : unicode | None
                Name for this RObject (if any)

            dic : dict | None
                Dict duck with initial data. Keys and values will be validated.

            special_keys : tuple
                Some keys can be marked as 'special' (whatever that means for you). Yes, yes... ugly as shit.
                This is just a convenience and serves as documentation, changing this value modifies nothing.
        """
        self.name = name
        self._d = {}
        if dic:
            for k,v in dic.iteritems():
                self[k] = v

    def _validate_key(self, k):
        if not isinstance(k, self.key_types):
            raise TypeError('invalid key type: %s - valid types: %s' % (repr(k), self.key_types))

    def _validate_value(self, v):
        if isinstance(v, RObject):
            if not self.allow_nested_single:
                raise TypeError('invalid value type: %s' % repr(v))
        elif isinstance(v, self.value_types_nested_collection):
            for x in v:
                self._validate_value(x)
        elif not isinstance(v, self.value_types_simple):
            raise TypeError('invalid value type: %s' % repr(v))

    def __repr__(self):
        return u'<%s %s: %s>' % (self.__class__.__name__, repr(self.name), super(RObject, self).__repr__())


    # dict protocol

    def __setitem__(self, k, v):
        self._validate_key(k)
        self._validate_value(v)
        self._d[k] = v

    def update(self, dic):
        for k,v in dic.iteritems():
            self[k] = v

    def setdefault(self, k, v):
        try:
            return self._d[k]
        except KeyError:
            self[k] = v
        return self._d[k]

    keys         = lambda self:    self._d.keys()
    iterkeys     = lambda self:    self._d.iterkeys()
    values       = lambda self:    self._d.values()
    itervalues   = lambda self:    self._d.itervalues()
    items        = lambda self:    self._d.items()
    iteritems    = lambda self:    self._d.iteritems()
    __iter__     = lambda self:    self._d.__iter__()
    __len__      = lambda self:    self._d.__len__()
    __contains__ = lambda self, k: self._d.__contains__(k)
    __getitem__  = lambda self, k: self._d.__getitem__(k)
    __delitem__  = lambda self, k: self._d.get(k)
    get          = lambda self, k: self._d.get(k)
    pop          = lambda self, k: self._d.get(k)


