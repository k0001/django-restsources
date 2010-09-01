# -*- coding: utf8 -*-,

import re

from django.http import HttpResponse, Http404
from django.db.models import ObjectDoesNotExist

from .restponders import RestponderSet
from .restponse import Restponse
from .restsource import Restsource

__all__ = 'Handler',


_RE_MIMETYPE = re.compile(r'[-+*\w]+/[-+*\w]+')


class RestsourceDoesNotExist(Exception):
    pass


class Handler(object):
    def __init__(self, restsource, restponders, single=False, restponder_param='format', fallback_restponder=None):
        if not isinstance(restsource, Restsource):
            raise TypeError(type(restsource))
        self.restsource = restsource
        self.single = single
        self.restponder_param = restponder_param
        self._restponders = RestponderSet(restponders)
        if fallback_restponder:
            self._fallback_restponder = self._restponders.get_by_extension(fallback_restponder)
        else:
            self._fallback_restponder = iter(self._restponders).next() # just pick any

    def select_restponder(self, request, extension=None):
        if extension:
            # The user explicitly requested a representation format, so it's ok to 404 if not available
            try:
                return self._restponders.get_by_extension(extension)
            except KeyError:
                raise Http404(u"Invalid representation requested: %s" % extension)

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

    def __call__(self, request, **kwargs):
        restponder_extension = kwargs.pop(self.restponder_param, request.REQUEST.get(self.restponder_param))
        restponder = self.select_restponder(request, restponder_extension)
        if not restponder:
            options = u"\n".join(u" - %s: %s" % (x.extension, x.mimetype) for x in self._restponders)
            return HttpResponse(u"Can't satisfy requested media type. Valid options:\n%s" % options,
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

        try:
            restponse = meth(request, **kwargs)
        except (ObjectDoesNotExist, RestsourceDoesNotExist):
            raise Http404(u"No %s found matching the query" % self.restsource.name)

        assert isinstance(restponse, Restponse)

        response = HttpResponse()
        restponder.write_headers(restponse, response)
        if request.method != 'HEAD':
            restponder.write_body(restponse, response)

        return response
