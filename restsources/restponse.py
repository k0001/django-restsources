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
    ERROR_BAD_REQUEST = "ERROR_BAD_REQUEST"

    # server errors
    ERROR_INTERNAL = "ERROR_INTERNAL"


class Restponse(object):

    def __init__(self, status=RESTPONSE_STATUS.OK, payload=None,
                 info=None, http_status=200, http_headers=()):
        self.status = status
        self.payload = payload
        self.info = info
        self.http_status = http_status
        self.http_headers = set()
        for k,v in http_headers:
            self.http_headers.add((k, v))

    def _set_payload(self, value):
        if not isinstance(value, (RestsourceValueObject, RestsourceValueObjectCollection)) and value is not None:
            raise TypeError(type(value))
        self._payload = value

    payload = property(lambda self: self._payload, _set_payload)


