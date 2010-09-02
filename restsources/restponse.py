# -*- coding: utf8 -*-

from .restsource_value import RestsourceValueObject, RestsourceValueObjectCollection
from .exceptions import ResourceDoesNotExist, MultipleResourcesExist

__all__ = 'Restponse', 'RESTPONSE_STATUS',

class RESTPONSE_STATUS(object):
    OK = "OK"

    # client errors
    ERROR_NOT_FOUND = "ERROR_NOT_FOUND"
    ERROR_DUPLICATES = "ERROR_DUPLICATES"
    ERROR_CONFLICT = "ERROR_CONFLICT"

    # server errors
    ERROR_INTERNAL = "ERROR_INTERNAL"


class Restponse(object):

    def __init__(self, status=RESTPONSE_STATUS.OK, payload=None, http_status=200, http_headers=()):
        self._status, self._payload, self._http_headers = None, None, set()

        self.status = status
        self.payload = payload
        self.http_status = http_status
        for k,v in http_headers:
            self.http_headers.add((k, v))

    http_headers = property(lambda self: self._http_headers)

    def _set_status(self, value):
        assert isinstance(value, str)
        self._status = value

    status = property(lambda self: self._status, _set_status)

    def _set_payload(self, value):
        if not isinstance(value, (RestsourceValueObject, RestsourceValueObjectCollection)) and value is not None:
            raise TypeError(type(value))
        self._payload = value

    payload = property(lambda self: self._payload, _set_payload)


