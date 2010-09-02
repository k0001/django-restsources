# -*- coding: utf8 -*-

from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import Paginator, InvalidPage

from .restponse import Restponse, RESTPONSE_STATUS
from .restsource_value import RestsourceValue, RestsourceValueObject, RestsourceValueObjectCollection
from restsources.exceptions import ResourceDoesNotExist, MultipleResourcesExist

__all__ = 'Restsource',


class Restsource(object):
    methods = 'GET',
    model = None
    fields = ()
    excluded = 'pk',
    attributes = ()

    ### Querying

    def queryset(self):
        if self.model:
            return self.model.objects.all()

    def filter(self, **kwargs):
        """Returns a iterable of matching resource objects"""
        qs = self.queryset()
        if not qs:
            raise NotImplementedError()
        return qs.filter(**kwargs)

    def get(self, **kwargs):
        """Returns a single resource object"""
        l = self.filter(**kwargs)
        if isinstance(l, QuerySet):
            try:
                return l.get()
            except ObjectDoesNotExist:
                raise ResourceDoesNotExist()
        try:
            if len(l) > 1:
                raise MultipleResourcesExist()
            return iter(l).next()
        except TypeError:
            raise ResourceDoesNotExist()

    def get_page(self, objs, per_page, page_num):
        paginator = Paginator(objs, per_page, allow_empty_first_page=True)
        return paginator.page(page_num)


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

    def GET(self, options, request, params):
        if options['single']:
            return Restponse(payload=self.dump_single(self.get(**params)))
        objs = self.filter(**params)
        if options['paginate_by']:
            return self._get_paginated_restponse(objs, options, request, params)
        return Restponse(payload=self.dump_collection(objs))

    def POST(self, options, request, params):
        raise NotImplementedError

    def PUT(self, options, request, params):
        raise NotImplementedError

    def DELETE(self, options, request, params):
        raise NotImplementedError


    # Utils
    def _get_paginated_restponse(self, objs, options, request, params):
        try:
            page_num = int(params.get(options['page_qparam'], request.REQUEST.get(options['page_qparam'], 1)))
            page = self.get_page(objs, options['paginate_by'], page_num)
        except (ValueError, InvalidPage):
            return Restponse(status=RESTPONSE_STATUS.ERROR_BAD_REQUEST, info=u"Invalid page.", http_status=400)
        return Restponse(payload=self.dump_collection(page.object_list))
