# -*- coding: utf8 -*-

from __future__ import absolute_import

try:
    import cPickle as pickle
except ImportError:
    import pickle

from datetime import datetime, date

from ..restsource import RObject, RObjectList
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
            "payload": self._format_payload(restponse.payload) }
        if restponse.info:
            out["info"] = restponse.info
        if restponse.links:
            out["links"] = []
            for href, attrs in restponse.links:
                d = { 'href': href }
                d.update(attrs)
                out['links'].append({'link': d})
        return out

    def _format_payload(self, payload):
        if payload is not None:
            return self._format_robject(payload)

    def _format_robject(self, ro):
        if isinstance(ro, RObjectList):
            if ro.name is None:
                return [self._format_robject(x) for x in ro]
            return { ro.name: [self._format_robject(x) for x in ro] }
        elif isinstance(ro, RObject):
            d = {}
            for k,v in ro.iteritems():
                if isinstance(v, (RObject, RObjectList)):
                    d[k] = self._format_robject(v)
                elif isinstance(v, (date, datetime)):
                    d[k] = v.isoformat()
                elif isinstance(v, (unicode, str, int, long, float)) or v is None:
                    d[k] = v
                else:
                    raise TypeError(v)
            if ro.name is None:
                return d
            return { ro.name: d }
        else:
            raise TypeError(ro)


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



