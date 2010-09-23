# -*- coding: utf8 -*-,

import re
import sys
import traceback

from django.conf import settings
from django.http import HttpResponse, Http404
from django.db.models import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

from .restponders import RestponderSet, RestponderRequestValidationError
from .restponse import Restponse, RESTPONSE_STATUS
from .restsource import Restsource
from .exceptions import ResourceDoesNotExist, MultipleResourcesExist
from .utils import load_put_and_files


__all__ = 'Handler',


_RE_MIMETYPE = re.compile(r'[-+*\w]+/[-+*\w]+')
_REQUEST_ENTITY_MIMETYPES = 'application/x-www-form-urlencoded', 'multipart/form-data',


class Handler(object):
    def __init__(self, restponders, options=None, options_param='handler_options'):
        self._restponders = RestponderSet(restponders)
        self._fallback_restponder = restponders[0]

        # Expected options:
        #
        # restsource:
        #   Restsource instance
        #
        # single: (default False)
        #   Whether to return a single result object, or a collection of them.
        #
        # restponder_name_qparam: (default 'format')
        #   Querystring parameter name for restponder selection
        #
        # restponder_name_uparam: (default None)
        #   URL parameter name for restponder selection. If specified, overrides restponder_name_qparam
        #
        # paginate_by: (default None)
        #   If different than None, then paginate the results.
        #
        # page_qparam: (default 'page')
        #   Querystring parameter name for page number selection if pagination is enabled (see paginate_by).

        self._options = {
            'single': False,
            'restponder_name_uparam': None,
            'restponder_name_qparam': 'format',
            'paginate_by': None,
            'page_qparam': 'page'
        }
        if options:
            self._options.update(options)
        self._options_param = options_param

    @csrf_exempt
    def __call__(self, request, **kwargs):
        options = self._options.copy()
        options.update(kwargs.pop(self._options_param, {}))
        restsource = options['restsource']

        # Restponder selection
        restponder = self.select_restponder(options, request, kwargs)
        if not restponder:
            s = u"\n".join(u" - %s: %s" % (x.name, x.mimetype) for x in self._restponders)
            return HttpResponse(u"Can't satisfy requested media type. Valid options:\n%s" % s,
                                status=406, mimetype='text/plain')

        # Method selection
        if request.method == 'HEAD':
            meth_name = 'GET'
        else:
            meth_name = request.method
        if not meth_name in restsource.methods:
            response = HttpResponse(status=405, mimetype=restponder.content_type)
            response['Allow'] = ', '.join(restsource.methods)
            if request.method == 'OPTIONS':
                response.status_code = 200
            return response
        meth = getattr(restsource, meth_name)

        # Request entity validation
        if meth_name in ('PUT', 'POST'):
            for mimetype in _RE_MIMETYPE.findall(request.META['CONTENT_TYPE']):
                if mimetype in _REQUEST_ENTITY_MIMETYPES:
                    break
            else:
                return HttpResponse(u"Supported media types: %s" % u", ".join(_REQUEST_ENTITY_MIMETYPES),
                                    status=415, mimetype='text/plain')
            if meth_name == 'PUT':
                # Handle PUT entity just like Django does for POST
                load_put_and_files(request)

        # Request restponder validation
        try:
            restponder.validate_request(request)
        except RestponderRequestValidationError, e:
            return HttpResponse(u"Invalid '%s: %s' request: %s" % (restponder.name, restponder.mimetype, unicode(e)),
                                status=404, mimetype='text/plain')

        # Restponse
        try:
            restponse = meth(options, request, kwargs)
            assert isinstance(restponse, Restponse)
        except ResourceDoesNotExist:
            restponse = Restponse(status=RESTPONSE_STATUS.ERROR_NOT_FOUND, http_status=404)
        except MultipleResourcesExist:
            restponse = Restponse(status=RESTPONSE_STATUS.ERROR_CONFLICT, http_status=409)
        except Exception, e:
            if settings.DEBUG:
                raise
            self.log_exception(request.META['wsgi.errors'], sys.exc_info())
            restponse = Restponse(status=RESTPONSE_STATUS.ERROR_INTERNAL, http_status=500)

        # HTTP Response
        return self.make_response(request, restponse, restponder)


    def select_restponder(self, options, request, params):
        if options["restponder_name_uparam"]:
            name = params.pop(options["restponder_name_uparam"])
        else:
            name = request.GET.get(options["restponder_name_qparam"])

        if name:
            # The user explicitly requested a representation format, so it's ok to 404 if not available
            try:
                return self._restponders.get_by_name(name)
            except KeyError:
                raise Http404(u"Invalid representation requested: %s" % name)

        elif request.META.get('HTTP_ACCEPT'):
            # Try to find a valid mimetype in HTTP Accept header
            # TODO We are ignoring '*' and 'q' [RFC 2616 Section 14.1]
            for mimetype in _RE_MIMETYPE.findall(request.META['HTTP_ACCEPT']):
                try:
                    return self._restponders.get_by_mimetype(mimetype)
                except KeyError:
                    continue
            else:
                # We don't have any of the representations supported by the client.
                return None

        # From [RFC 2616 Section 14.1]:
        # If no Accept header field is present, then it is assumed that the client accepts all media types.
        return self._fallback_restponder


    def make_response(self, request, restponse, restponder):
        response = HttpResponse()
        restponder.write_headers(request, response, restponse)
        if request.method != 'HEAD':
            restponder.write_body(request, response, restponse)
        return response


    def log_exception(self, stderr, exc_info):
        """Log the 'exc_info' tuple in the server log"""
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, stderr)
        stderr.flush()
