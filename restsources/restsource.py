# -*- coding: utf8 -*-

from .restponse import Restponse
from .restsource_value import RestsourceValue, RestsourceValueObject, RestsourceValueObjectCollection

__all__ = 'Restsource',


class Restsource(object):
    model = None
    attributes = ()
    fields = ()
    excluded = ('pk',)


    ### Querying

    def queryset(self):
        if self.model:
            return self.model.objects.all()

    def filter(self, **kwargs):
        qs = self.queryset()
        if not qs:
            raise NotImplementedError
        return qs.filter(**kwargs)

    def get(self, **kwargs):
        return self.filter(**kwargs).get()


    ### Field values

    def _get_field_value(self, obj, field_name):
        try:
            meth = getattr(self, 'get_%s' % field_name)
            value = meth(obj)
        except AttributeError:
            value = getattr(obj, field_name)
        return value

    def _get_field_restsourcevalue(self, obj, field_name):
        value = self._get_field_value(obj, field_name)
        if value is not None:
            value = RestsourceValue.get_for_value(value)
        return value

    def _get_fields_values(self, obj):
        values = {}
        for field_name in set(self.attributes + self.fields) - set(self.excluded):
            values[field_name] = self._get_field_value(obj, field_name)
        return values

    def _get_fields_restsourcevalues(self, obj):
        restsourcevalues = {}
        for k,v in self._get_fields_values(obj).items():
            restsourcevalues[RestsourceValue.get_for_value(k)] = RestsourceValueObject.get_for_value(v)
        return restsourcevalues


    ### Dumping Restsources

    def dump_single(self, obj):
        data = self._get_fields_restsourcevalues(obj)
        return RestsourceValueObject(self.name, data, self.attributes)

    def dump_collection(self, objs):
        data = [self.dump_single(x) for x in objs]
        return RestsourceValueObjectCollection(self.name_plural, data)


    ### HTTP requests handling

    def GET(self, request, **kwargs):
        out = self.filter(**kwargs)
        return Restponse(payload=self.dump_collection(out))

    def GET_single(self, request, **kwargs):
        out = self.get(**kwargs)
        return Restponse(payload=self.dump_single(out))

    def POST(self, request, **kwargs):
        raise NotImplementedError

    def PUT(self, request, **kwargs):
        raise NotImplementedError

    def DELETE(self, request, **kwargs):
        raise NotImplementedError

    # These values are used by the ``allowed_methods`` property
    POST.disabled = True
    PUT.disabled = True
    DELETE.disabled = True

    @property
    def allowed_methods(self):
        """Return the HTTP methods allowed for this resource"""
        allow = []
        if getattr(self.GET, 'disabled', False) or getattr(self.GET_single, 'disabled', False):
            options.append('GET')
            options.append('HEAD')
        if getattr(self.POST, 'disabled', False):
            options.append('POST')
        if getattr(self.PUT, 'disabled', False):
            options.append('PUT')
        if getattr(self.DELETE, 'disabled', False):
            options.append('DELETE')
        return tuple(allow)


    # Utils

    def handler(self, **kwargs):
        from .handler import Handler
        return Handler(self, **kwargs)

