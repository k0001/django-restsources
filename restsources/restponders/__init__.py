# -*- coding: utf8 -*-

__all__ = 'Restponder', 'registry'


class Restponder(object):
    extension = 'SET THIS TO THE PREFERED FILE EXTENSION'
    mimetype = 'SET THIS TO THE PREFERED MIMETYPE'
    encoding = 'utf8'

    @property
    def content_type(self):
        return '%s; charset=%s' % (self.mimetype, self.encoding)

    def write_headers(self, restponse, response):
        response.status = restponse.http_status
        response['Content-Type'] = self.content_type
        for k,v in restponse.http_headers:
            response[k] = v

    def write_body(self, restponse, response):
        raise NotImplementedError

    @classmethod
    def format_restsourcevalue(cls, rv):
        raise NotImplementedError


class RestponderRegistry(object):
    def __init__(self):
        self._registry = []

    def register(self, restponder):
        assert isinstance(restponder, Restponder)
        if restponder in self._registry:
            raise ValueError(u"%s already registered." % repr(restponder))
        self._registry.append(restponder)

    def unregister(self, restponder):
        if isinstance(restponder, Restponder):
            self._registry.remove(restponder)
        elif isinstance(restponder, basestring):
            if '/' in restponder:
                self._registry.remove(self.get_by_mimetype(restponder))
            else:
                self._registry.remove(self.get_by_extension(restponder))
        else:
            raise KeyError(restponder)

    def clear(self):
        self._registry[:] = []

    def get_default(self):
        if self._registry:
            return self._registry[0]

    def get_by_extension(self, extension):
        for x in self._registry:
            if x.extension == extension:
                return x
        raise KeyError(extension)

    def get_by_mimetype(self, mimetype):
        for x in self._registry:
            if x.mimetype == mimetype:
                return x
        raise KeyError(mimetype)


registry = RestponderRegistry()
