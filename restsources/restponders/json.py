# -*- coding: utf8 -*-

from __future__ import absolute_import

try:
    import simplejson as json
except ImportError:
    import json


from ..restsource_value import (RestsourceValueUnicode, RestsourceValueBytes,
                                RestsourceValueInteger, RestsourceValueFloat,
                                RestsourceValueObject, RestsourceValueObjectCollection)
from . import Restponder, registry

__all__ = 'JSONRestponder',


class JSONRestponder(Restponder):
    extension = 'json'
    mimetype = 'application/json'
    mimetype = 'text/plain'

    def __init__(self, indent=None, encoding='utf8'):
        self.indent = indent
        self.encoding = encoding

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        json.dump(data, response, indent=self.indent, encoding=self.encoding)
        return response

    def _format_restponse(self, restponse):
        out = {
            "status": restponse.status,
            "payload": self.format_restsourcevalue(restponse.payload)
        }
        if restponse.message:
            out["message"] = restponse.message
        return out

    @classmethod
    def format_restsourcevalue(cls, rv):
        if rv is None:
            return None
        elif isinstance(rv, (RestsourceValueUnicode, RestsourceValueBytes,
                             RestsourceValueInteger, RestsourceValueFloat)):
            return rv.value
        elif isinstance(rv, RestsourceValueObject):
            return { rv.value['name']: dict((cls.format_restsourcevalue(k), cls.format_restsourcevalue(v))
                                            for (k,v) in rv.value['data'].items()) }
        elif isinstance(rv, RestsourceValueObjectCollection):
            return { rv.value['name']: [cls.format_restsourcevalue(x) for x in rv.value['collection']] }
        raise TypeError(type(rv))


registry.register(JSONRestponder())

