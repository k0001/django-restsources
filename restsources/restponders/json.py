# -*- coding: utf8 -*-

from __future__ import absolute_import
from functools import partial
import re

from django.conf import settings
from django.utils.encoding import smart_str

from ..restponse import Restponse, RESTPONSE_STATUS
from . import RestponderRequestValidationError
from .python import PythonRestponder
from .json_util import json, JSON


if settings.DEBUG: # Indent JSON if in DEBUG mode
    try:
        import simplejson
    except ImportError:
        pass
    else:
        json = JSON(simplejson, partial(simplejson.dumps, indent=1), simplejson.loads)


__all__ = 'JSONRestponder', 'JSONPRestponder',


_RE_JS_FUNCTION_NAME = re.compile(r'^\w+$')


class JSONRestponder(PythonRestponder):
    name = 'json'
    mimetype = 'application/json'

    def write_body(self, request, response, restponse):
        data = self._format_restponse(restponse)
        response.write(json.dumps(data))


class JSONPRestponder(JSONRestponder):
    name = 'jsonp'
    mimetype = 'application/javascript'
    jsonp_callback_qparam = 'jsonp_callback'

    def validate_request(self, request):
        jsonp_callback = request.GET.get(self.jsonp_callback_qparam, u'')
        if not _RE_JS_FUNCTION_NAME.match(jsonp_callback):
            raise RestponderRequestValidationError(u"Invalid value for '%s'" % self.jsonp_callback_qparam)

    def write_body(self, request, response, restponse):
        jsonp_callback = request.GET[self.jsonp_callback_qparam]
        data = self._format_restponse(restponse)
        jsonp = "%s(%s);" % (smart_str(jsonp_callback, self.encoding), json.dumps(data))
        response.write(jsonp)

