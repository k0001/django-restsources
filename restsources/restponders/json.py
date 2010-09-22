# -*- coding: utf8 -*-

from __future__ import absolute_import
from functools import partial

from django.conf import settings

from .python import PythonRestponder
from .json_util import json, JSON


if settings.DEBUG: # Indent JSON if in DEBUG mode
    try:
        import simplejson
    except ImportError:
        pass
    else:
        json = JSON(simplejson, partial(simplejson.dumps, indent=1), simplejson.loads)


__all__ = 'JSONRestponder',


class JSONRestponder(PythonRestponder):
    name = 'json'
    mimetype = 'application/json'

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        response.write(json.dumps(data))
        return response


