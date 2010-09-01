# -*- coding: utf8 -*-

from __future__ import absolute_import

import xml.etree.ElementTree as ET

from ..restsource_value import (RestsourceValueUnicode, RestsourceValueBytes,
                                RestsourceValueInteger, RestsourceValueFloat,
                                RestsourceValueDate, RestsourceValueDatetime,
                                RestsourceValueObject, RestsourceValueObjectCollection)
from . import Restponder

__all__ = 'XMLRestponder',


class XMLRestponder(Restponder):
    extension = 'xml'
    mimetype = 'application/xml'

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        xml = ET.tostring(data, self.encoding)
        response.write(xml)
        return response

    def _format_restponse(self, restponse):
        root = ET.Element(u"resource", { u"status": unicode(restponse.status) })
        if restponse.message:
            root.set(u"message", restponse.message)
        root.insert(0, self._format_payload(restponse.payload))
        return root

    def _format_payload(self, payload):
        el = ET.Element(u"payload")
        el.insert(0, self.format_restsourcevalue(payload))
        return el

    @classmethod
    def _format_simple_restsourcevalue_as_text(cls, rv):
        if rv is None:
            return None
        if isinstance(rv, (RestsourceValueUnicode, RestsourceValueBytes)):
            return rv.value
        elif isinstance(rv, (RestsourceValueInteger, RestsourceValueFloat)):
            return srt(rv.value)
        elif isinstance(rv, (RestsourceValueDate, RestsourceValueDatetime)):
            return rv.value.isoformat()
        raise TypeError(type(rv))

    @classmethod
    def _format_simple_restsourcevalue_as_element(cls, name, rv):
        el = ET.Element(name)
        el.text = cls._format_simple_restsourcevalue_as_text(rv)
        return el

    @classmethod
    def format_restsourcevalue(cls, rv):
        if isinstance(rv, RestsourceValueObject):
            el = ET.Element(rv.value['name'])
            attributes, data = rv.value['attributes'], dict((k.value, v) for (k,v) in rv.value['data'].items())
            for attr in attributes:
                el.set(attr, cls._format_simple_restsourcevalue_as_text(data[attr]))
            for i,(k,rv) in enumerate(((x,y) for (x,y) in data.items() if not x in attributes)):
                if isinstance(rv, (RestsourceValueUnicode, RestsourceValueBytes,
                                   RestsourceValueInteger, RestsourceValueFloat,
                                   RestsourceValueDate, RestsourceValueDatetime)):
                    el.insert(i, cls._format_simple_restsourcevalue_as_element(k, rv))
                elif isinstance(rv, (RestsourceValueObject, RestsourceValueObjectCollection)):
                    el.insert(i, cls.format_restsourcevalue(rv))
                else:
                    raise TypeError(type(rv))
            return el
        elif isinstance(rv, RestsourceValueObjectCollection):
            el = ET.Element(rv.value['name'])
            for i,x in enumerate(rv.value['collection']):
                el.insert(i, cls.format_restsourcevalue(x))
            return el
        raise TypeError(type(rv))


