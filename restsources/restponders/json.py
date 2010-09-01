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

    def __init__(self, compact=None, encoding='utf8'):
        self._json_dump_kwargs = { 'encoding': encoding, 'cls': _JSONEncoder }
        if compact:
            self._json_dump_kwargs['indent'] = None
            self._json_dump_kwargs['separators'] = ',', ':'
        else:
            self._json_dump_kwargs['indent'] = 1

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        self._json_dump(data, response)
        return response

    def _json_dump(self, obj, fp):
        return json.dump(obj, fp, **self._json_dump_kwargs)

    def _format_restponse(self, restponse):
        out = {
            "status": restponse.status,
            "payload": self.format_restsourcevalue(restponse.payload) }
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


