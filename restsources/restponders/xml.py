# -*- coding: utf8 -*-

from __future__ import absolute_import

import xml.etree.ElementTree as ET

from ..restsource_value import (Unicode, Bytes,
                                Integer, Float,
                                Date, Datetime,
                                Object, ObjectCollection)
from . import Restponder

__all__ = 'XMLRestponder',


class XMLRestponder(Restponder):
    name = 'xml'
    mimetype = 'application/xml'

    def write_body(self, restponse, response):
        data = self._format_restponse(restponse)
        xml = ET.tostring(data, self.encoding)
        response.write(xml)
        return response

    def _format_restponse(self, restponse):
        root = ET.Element(u"response", { u"status": restponse.status })
        if restponse.info:
            root.set(u"info", restponse.info)
        root.insert(0, self._format_payload(restponse.payload))
        if restponse.links:
            links = ET.Element(u"links")
            for i,(href,attrs) in enumerate(restponse.links):
                d = { 'href': href }
                d.update(attrs)
                links.insert(i, ET.Element(u"link", d))
            root.insert(0, links)
        return root

    def _format_payload(self, payload):
        el = ET.Element(u"payload")
        p = self.format_restsourcevalue(payload)
        if p:
            el.insert(0, p)
        return el

    @classmethod
    def _format_simple_restsourcevalue_as_text(cls, rv):
        if rv is None:
            return None
        if isinstance(rv, (Unicode, Bytes)):
            return rv.value
        elif isinstance(rv, (Integer, Float)):
            return str(rv.value)
        elif isinstance(rv, (Date, Datetime)):
            return rv.value.isoformat()
        raise TypeError(type(rv))

    @classmethod
    def _format_simple_restsourcevalue_as_element(cls, name, rv):
        el = ET.Element(name)
        el.text = cls._format_simple_restsourcevalue_as_text(rv)
        return el

    @classmethod
    def format_restsourcevalue(cls, rv):
        if rv is None:
            return None
        if isinstance(rv, Object):
            el = ET.Element(rv.value['name'])
            attributes, data = rv.value['primary_fields'], dict((k.value, v) for (k,v) in rv.value['data'].items())
            for attr in attributes:
                el.set(attr, cls._format_simple_restsourcevalue_as_text(data[attr]))
            for i,(k,rv) in enumerate(((x,y) for (x,y) in data.items() if not x in attributes)):
                if rv is None:
                    continue
                if isinstance(rv, (Unicode, Bytes,
                                   Integer, Float,
                                   Date, Datetime)):
                    el.insert(i, cls._format_simple_restsourcevalue_as_element(k, rv))
                elif isinstance(rv, (Object, ObjectCollection)):
                    el.insert(i, cls.format_restsourcevalue(rv))
                else:
                    raise TypeError(type(rv))
            return el
        elif isinstance(rv, ObjectCollection):
            el = ET.Element(rv.value['name'])
            for i,x in enumerate(rv.value['collection']):
                el.insert(i, cls.format_restsourcevalue(x))
            return el
        raise TypeError(type(rv))


