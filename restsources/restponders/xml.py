# -*- coding: utf8 -*-

from __future__ import absolute_import
from datetime import date, datetime
import xml.etree.ElementTree as ET

from django.utils.encoding import force_unicode

from . import Restponder
from ..robject import RObject, RObjectList

__all__ = 'XMLRestponder',


class XMLRestponder(Restponder):
    name = 'xml'
    mimetype = 'application/xml'

    def write_body(self, request, response, restponse):
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
        if payload:
            el.insert(0, self._format_robject(payload))
        return el


    def _format_robject(self, ro):
        if ro is None:
            return None

        # If ro.name is None, then we are being recursevily called
        # and the caller will override this name in [AAA] later
        el = ET.Element(force_unicode(ro.name))

        if isinstance(ro, RObject):
            for attr in ro.special_keys:
                el.set(attr, self._format_simple_value_as_text(ro[attr]))
            for i,(k,v) in enumerate((x,y) for (x,y) in ro.iteritems() if not x in ro.special_keys):
                if isinstance(v, (RObject, RObjectList)):
                    _child = self._format_robject(v)
                    _child.tag = force_unicode(k) # <-- [AAA]
                    el.insert(i, _child)
                else:
                    el.insert(i, self._format_simple_pair_as_element(k, v))
            return el

        elif isinstance(ro, RObjectList):
            for i,x in enumerate(ro):
                assert x.name is not None, u"I can't think of a situation where this could happen. Report this please."
                el.insert(i, self._format_robject(x))
            return el

        raise TypeError(ro)


    def _format_simple_value_as_text(self, value):
        if value is None:
            return None
        if isinstance(value, (date, datetime)):
            return force_unicode(value.isoformat())
        elif isinstance(value, (unicode, str, int, long, float)):
            return force_unicode(value)
        else:
            raise TypeError(value)


    def _format_simple_pair_as_element(self, name, value):
        el = ET.Element(force_unicode(name))
        el.text = self._format_simple_value_as_text(value)
        return el
