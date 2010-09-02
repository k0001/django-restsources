# -*- coding: utf8 -*-

from __future__ import absolute_import

from datetime import datetime, date

from .json_util import json

from ..restsource_value import (RestsourceValueUnicode, RestsourceValueBytes,
                                RestsourceValueInteger, RestsourceValueFloat,
                                RestsourceValueDate, RestsourceValueDatetime,
                                RestsourceValueObject, RestsourceValueObjectCollection)
from . import Restponder
from .python import PythonRestponder


__all__ = 'JSONRestponder',


class JSONRestponder(PythonRestponder):
    name = 'json'
    mimetype = 'application/json'

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        response.write(json.dumps(data))
        return response
