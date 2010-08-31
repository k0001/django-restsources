# -*- coding: utf8 -*-

from .restsource_value import RestsourceValueObject, RestsourceValueObjectCollection

__all__ = 'Restponse',


class Restponse(object):
    def __init__(self, status=0, message=None, payload=None,
                 http_status=200, http_headers=()):
        self._status, self._payload, self._http_headers = None, None, set()

        self.status = status
        self.message = message
        self.payload = payload
        self.http_status = http_status
        for k,v in http_headers:
            self.http_headers.add((k, v))

    http_headers = property(lambda self: self._http_headers)

    def _set_status(self, value):
        assert isinstance(value, int)
        self._status = value

    status = property(lambda self: self._status, _set_status)

    def _set_payload(self, value):
        if not isinstance(value, (RestsourceValueObject, RestsourceValueObjectCollection)) or value is None:
            raise TypeError(type(value))
        self._payload = value

    payload = property(lambda self: self._payload, _set_payload)


