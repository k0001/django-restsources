# -*- coding: utf8 -*-

from __future__ import absolute_import

try:
    import cPickle as pickle
except ImportError:
    import pickle

from datetime import datetime, date

from ..restsource_value import (RestsourceValueUnicode, RestsourceValueBytes,
                                RestsourceValueInteger, RestsourceValueFloat,
                                RestsourceValueDate, RestsourceValueDatetime,
                                RestsourceValueObject, RestsourceValueObjectCollection)
from . import Restponder

__all__ = 'PythonRestponder',


class PythonRestponder(Restponder):
    name = 'py'
    mimetype = 'application/x-python'

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        response.write(unicode(data).encode(self.encoding))
        return response

    def _format_restponse(self, restponse):
        out = {
            "status": restponse.status,
            "payload": self.format_restsourcevalue(restponse.payload) }
        if restponse.info:
            out["info"] = restponse.info
        if restponse.links:
            out["links"] = []
            for href, attrs in restponse.links:
                d = { 'href': href }
                d.update(attrs)
                out['links'].append({'link': d})
        return out

    @classmethod
    def format_restsourcevalue(cls, rv):
        if rv is None:
            return None
        elif isinstance(rv, (RestsourceValueUnicode, RestsourceValueBytes,
                             RestsourceValueInteger, RestsourceValueFloat)):
            return rv.value
        elif isinstance(rv, (RestsourceValueDate, RestsourceValueDatetime)):
            return rv.value.isoformat()
        elif isinstance(rv, RestsourceValueObject):
            return { rv.value['name']: dict((cls.format_restsourcevalue(k), cls.format_restsourcevalue(v))
                                            for (k,v) in rv.value['data'].items()) }
        elif isinstance(rv, RestsourceValueObjectCollection):
            return { rv.value['name']: [cls.format_restsourcevalue(x) for x in rv.value['collection']] }
        raise TypeError(type(rv))


class PythonPickleRestponder(PythonRestponder):
    name = 'py_pickle'
    mimetype = 'application/octet-stream'

    def __init__(self, protocol=2, *args, **kwargs):
        self.protocol = protocol
        super(PythonPickleRestponder, self).__init__(*args, **kwargs)

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        response.write(pickle.dumps(data, self.protocol))
        return response



