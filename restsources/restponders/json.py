# -*- coding: utf8 -*-

from __future__ import absolute_import

from datetime import datetime, date

from .json_util import json

from ..restsource_value import (RestsourceValueUnicode, RestsourceValueBytes,
                                RestsourceValueInteger, RestsourceValueFloat,
                                RestsourceValueDate, RestsourceValueDatetime,
                                RestsourceValueObject, RestsourceValueObjectCollection)
from . import Restponder

__all__ = 'JSONRestponder',


class JSONRestponder(Restponder):
    extension = 'json'
    mimetype = 'application/json'

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        response.write(json.dumps(data))
        return response

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

