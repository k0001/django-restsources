# -*- coding: utf8 -*-

__all__ = 'Restponder', 'RestponderSet'


class Restponder(object):
    name = 'SET THIS TO THE PREFERED FILE NAME'
    mimetype = 'SET THIS TO THE PREFERED MIMETYPE'
    encoding = 'utf8'

    def __init__(self, encoding='utf8'):
        self.encoding = encoding

    @property
    def content_type(self):
        return '%s; charset=%s' % (self.mimetype, self.encoding)

    def write_headers(self, restponse, response):
        response.status_code = restponse.http_status
        response['Content-Type'] = self.content_type
        for k,v in restponse.http_headers:
            response[k] = v

    def write_body(self, restponse, response):
        raise NotImplementedError

    @classmethod
    def format_restsourcevalue(cls, rv):
        raise NotImplementedError


class RestponderSet(object):
    def __init__(self, restponders):
        self._set = set()
        for x in restponders:
            self.add(x)

    def __iter__(self):
        return iter(self._set)

    def add(self, restponder):
        assert isinstance(restponder, Restponder)
        self._set.add(restponder)

    def remove(self, restponder):
        if isinstance(restponder, Restponder):
            self._set.remove(restponder)

        elif isinstance(restponder, basestring):
            if '/' in restponder:
                self._set.remove(self.get_by_mimetype(restponder))
            else:
                self._set.remove(self.get_by_name(restponder))
        else:
            raise KeyError(restponder)

    def clear(self):
        self._set.clear()

    def get_by_name(self, name):
        for x in self._set:
            if x.name == name:
                return x
        raise KeyError(name)

    def get_by_mimetype(self, mimetype):
        for x in self._set:
            if x.mimetype == mimetype:
                return x
        raise KeyError(mimetype)

