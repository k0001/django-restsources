# -*- coding: utf8 -*-

from __future__ import absolute_import

from datetime import datetime, date

try:
    import simplejson as json
except ImportError:
    import json


from ..restsource_value import (RestsourceValueUnicode, RestsourceValueBytes,
                                RestsourceValueInteger, RestsourceValueFloat,
                                RestsourceValueDate, RestsourceValueDatetime,
                                RestsourceValueObject, RestsourceValueObjectCollection)
from . import Restponder

__all__ = 'JSONRestponder',

class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return super(_JSONEncoder, self).default(o)


class JSONRestponder(Restponder):
    extension = 'json'
    mimetype = 'application/json'

    def __init__(self, indent=None, encoding='utf8'):
        self.indent = indent
        self.encoding = encoding

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        json.dump(data, response, indent=self.indent, encoding=self.encoding, cls=_JSONEncoder)
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
                             RestsourceValueInteger, RestsourceValueFloat,
                             RestsourceValueDate, RestsourceValueDatetime)):
            return rv.value
        elif isinstance(rv, RestsourceValueObject):
            return { rv.value['name']: dict((cls.format_restsourcevalue(k), cls.format_restsourcevalue(v))
                                            for (k,v) in rv.value['data'].items()) }
        elif isinstance(rv, RestsourceValueObjectCollection):
            return { rv.value['name']: [cls.format_restsourcevalue(x) for x in rv.value['collection']] }
        raise TypeError(type(rv))


