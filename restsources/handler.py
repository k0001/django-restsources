# -*- coding: utf8 -*-

import re

from django.http import HttpResponse, Http404

from .restponse import Restponse
from .restsource import Restsource
from .restponders import registry as restponders_registry

__all__ = 'Handler',


_RE_MIMETYPE = re.compile(r'[-+*\w]+/[-+*\w]+')

class Handler(object):
    def __init__(self, restsource, single=False, restponder_param=None):
        if not isinstance(restsource, Restsource):
            raise TypeError(type(restsource))
        self.restsource = restsource
        self.single = single
        self.restponder_param = restponder_param

    def select_restponder(self, request, extension=None):
        if extension:
            # The user explicitly requested a representation format, so it's ok to 404 if not available
            try:
                return restponders_registry.get_by_extension(extension)
            except KeyError:
                raise Http404(u"Invalid representation requested: %s" % extension)

        elif request.META.get('HTTP_ACCEPT'):
            # Try to find a valid mimetype in HTTP Accept header
            # TODO We are ignoring '*' and 'q' [RFC 2616 Section 14.1]
            for mimetype in _RE_MIMETYPE.findall(request.META['HTTP_ACCEPT']):
                try:
                    return restponders_registry.get_by_mimetype(mimetype)
                except KeyError:
                    continue
            else:
                # We don't have any of the representations supported by the client.
                return None

        # From [RFC 2616 Section 14.1]:
        # If no Accept header field is present, then it is assumed that the client accepts all media types.
        restponder = restponders_registry.get_default()
        if restponder:
            return restponder
        # You probably forgot to register at least one Restponder
        raise Http404(u"No valid representations available")

    def __call__(self, request, **kwargs):
        if self.restponder_param:
            restponder_extension = kwargs.pop(self.restponder_param, None)
        else:
            restponder_extension = None
        restponder = self.select_restponder(request, restponder_extension)
        if not restponder:
            return HttpResponse(u"Invalid representation requested",
                                status=400, mimetype='text/plain')

        meth_name = request.method
        if self.single:
            meth_name += '_single'
        try:
            meth = getattr(self.restsource, meth_name)
        except AttributeError:
            response = HttpResponse(status=405, mimetype=restponder.content_type)
            response['Allow'] = ', '.join(self.restsource.allowed_methods)
            if request.method == 'OPTIONS':
                response.status_code = 200
            return response

        restponse = meth(request, **kwargs)
        assert isinstance(restponse, Restponse)

        response = HttpResponse()
        restponder.write_headers(restponse, response)
        if request.method != 'HEAD':
            restponder.write_body(restponse, response)

        return response
