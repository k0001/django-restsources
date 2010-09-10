# -*- coding: utf8 -*-
import types

from django.db import models
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
    primary_fields = ()
    relations = None


    def __init__(self, primary_fields_only=False, excluded=()):
        self.excluded = tuple(set(tuple(self.excluded) + tuple(excluded)))
        self._primary_fields_only = primary_fields_only


    ### Querying

    def queryset(self):
        """
        Default query set for this Resource.

        Note that this isn't restricted to return a Django QuerySet. You could return
        whatever works for you as a "query set", just make sure you make good
        use of it in methods ``filter`` and ``get``.
        """
        if self.model:
            return self.model.objects.all()
        raise NotImplementedError

    def filter(self, queryset, request, **kwargs):
        """Returns a iterable of matching resource objects"""
        return queryset.filter(**kwargs)

    def get(self, queryset, request, **kwargs):
        """Returns a single resource object"""
        l = self.filter(queryset, request, **kwargs)
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


    ### Field values

    def _get_field_value(self, obj, field_name):
        if hasattr(self, 'get_%s' % field_name):
            meth = getattr(self, 'get_%s' % field_name)
            value = meth(obj)
        else:
            value = getattr(obj, field_name)
        return value

    def _get_field_restsourcevalue(self, obj, field_name):
        value = self._get_field_value(obj, field_name)
        if value is not None:
            value = RestsourceValue.get_for_value(value)
        return value

    def _get_fields_values(self, obj, primary_fields_only=False):
        field_names = set(self.primary_fields)
        if not primary_fields_only:
            field_names.update(self.fields)
        field_names.difference_update(self.excluded)
        values = {}
        for field_name in field_names:
            values[field_name] = self._get_field_value(obj, field_name)
        return values

    def _get_fields_restsourcevalues(self, obj, primary_fields_only=False):
        if isinstance(obj, models.Model):
            return self._get_fields_restsourcevalues_for_model(obj, primary_fields_only)
        restsourcevalues = {}
        for k,v in self._get_fields_values(obj, primary_fields_only).iteritems():
            restsourcevalues[RestsourceValue.get_for_value(k)] = RestsourceValueObject.get_for_value(v)
        return restsourcevalues

    def _get_fields_restsourcevalues_for_model(self, obj, primary_fields_only=False):
        restsourcevalues = {}
        for k,v in self._get_fields_values(obj, primary_fields_only).iteritems():
            if v is None:
                rv = None
            elif isinstance(v, models.Manager):
                # Reverse FK or Reverse M2M
                rv = RestsourceValueObjectCollection(k, [self._rel(k).dump_single(x) for x in v.all()])
            else:
                try:
                    rv = RestsourceValueObject.get_for_value(v)
                except TypeError:
                    field, model, direct, m2m = obj._meta.get_field_by_name(k)
                    if isinstance(field, models.ForeignKey):
                        # Foreign Key
                        rv = self._rel(k).dump_single(v)
                    else:
                        raise
            restsourcevalues[RestsourceValue.get_for_value(k)] = rv
        return restsourcevalues


    def _rel(self, name):
        """Returns the Restsource asociated with a relationship"""
        try:
            return self.relations[name]
        except KeyError:
            raise RuntimeError(u"You need to specify a Restource for %s in %s.relations" % (name, self))
        except TypeError:
            # we enter here only the first time if self.relations isn't a dict, and we populate it.
            if isinstance(self.relations, types.MethodType):
                self.relations = self.relations() # overwrite
            elif self.relations is None:
                self.relations = {}
            return self._rel(name)

    ### Dumping Restsources

    def dump_single(self, obj):
        data = self._get_fields_restsourcevalues(obj, self._primary_fields_only)
        used_primary_fields = set(self.primary_fields) - set(self.excluded)
        return RestsourceValueObject(self.name, data, used_primary_fields)

    def dump_collection(self, objs):
        data = [self.dump_single(x) for x in objs]
        return RestsourceValueObjectCollection(self.name_plural, data)


    ### HTTP requests handling

    def GET(self, options, request, params):
        if options['single']:
            return Restponse(payload=self.dump_single(self.get(self.queryset(), request, **params)))
        objs = self.filter(self.queryset(), request, **params)
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
        assert request.method == 'GET', u"Paginating %s request not supported." % request.method
        page_qparam = options['page_qparam']
        try:
            page_num = int(params.get(page_qparam, request.REQUEST.get(page_qparam, 1)))
            paginator = Paginator(objs, options['paginate_by'], allow_empty_first_page=True)
            page = paginator.page(page_num)
        except (ValueError, InvalidPage):
            return Restponse(status=RESTPONSE_STATUS.ERROR_BAD_REQUEST, info=u"Invalid page.", http_status=400)
        restponse = Restponse(payload=self.dump_collection(page.object_list))


        ## Link headers
        qd = request.GET.copy()
        # rel first
        qd[page_qparam] = 1
        restponse.links.append(('%s?%s' % (request.path, qd.urlencode()), {'rel': 'first'}))
        # rel last
        qd[page_qparam] = paginator.num_pages
        restponse.links.append(('%s?%s' % (request.path, qd.urlencode()), {'rel': 'last'}))
        # rel previous
        if page.has_previous():
            qd[page_qparam] = page_num - 1
            restponse.links.append(('%s?%s' % (request.path, qd.urlencode()), {'rel': 'previous'}))
        # rel next
        if page.has_next():
            qd[page_qparam] = page_num + 1
            restponse.links.append(('%s?%s' % (request.path, qd.urlencode()), {'rel': 'next'}))

        return restponse


