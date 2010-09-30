# -*- coding: utf8 -*-
import types

from django.db import models
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import Paginator, InvalidPage
from django.utils.encoding import force_unicode

from .restponse import Restponse, RESTPONSE_STATUS
from .robject import RObject, RObjectList
from .exceptions import ResourceDoesNotExist, MultipleResourcesExist

__all__ = 'Restsource',


class Restsource(object):
    methods = 'GET',
    model = None
    fields = ()
    excluded = 'pk',
    primary_fields = ()
    relations = None


    def __init__(self, primary_fields_only=False, excluded=None, fields=None, primary_fields=None):
        if fields:
            self.fields = fields
        if primary_fields:
            self.primary_fields = primary_fields
        self.excluded = tuple(set(tuple(self.excluded) + tuple(excluded or ())))
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


    def _get_fields_values(self, obj, primary_fields_only=False):
        field_names = set(self.primary_fields)
        if not primary_fields_only:
            field_names.update(self.fields)
        field_names.difference_update(self.excluded)
        values = {}
        for field_name in field_names:
            values[field_name] = self._get_field_value(obj, field_name)
        return values


    def _get_robject(self, name, obj, primary_fields_only=False):
        if name is not None:
            name = force_unicode(name)
        ro = RObject(name)
        for k,v in self._get_fields_values(obj, primary_fields_only).iteritems():
            k = force_unicode(k)
            try:
                ro[k] = v
            except TypeError:
                if isinstance(v, models.Manager):
                    # Reverse FK or Reverse M2M
                    ro[k] = self._rel(k).dump_collection(v.all(), named=False)
                elif isinstance(v, models.Model):
                    ro[k] = self._rel(k).dump_single(v, named=False)
        ro.special_keys = tuple(set(ro.keys()) & set(self.primary_fields))
        return ro


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

    def dump_single(self, obj, named=True):
        name = self.name if named else None
        return self._get_robject(name, obj, self._primary_fields_only)

    def dump_collection(self, objs, named=True):
        name = self.name_plural if named else None
        return RObjectList(name, [self.dump_single(x) for x in objs])


    ### HTTP requests handling

    def GET(self, options, request, params):
        if options['single']:
            return Restponse(status=RESTPONSE_STATUS.OK, http_status=200,
                             payload=self.dump_single(self.get(self.queryset(), request, **params)))
        objs = self.filter(self.queryset(), request, **params)
        if options['paginate_by']:
            return self._get_paginated_restponse(objs, options, request, params)
        return Restponse(status=RESTPONSE_STATUS.OK, http_status=200, payload=self.dump_collection(objs))

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
        restponse = Restponse(status=RESTPONSE_STATUS.OK, http_status=200,
                              payload=self.dump_collection(page.object_list))

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

