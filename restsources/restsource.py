# -*- coding: utf-8 -*-
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
    relations = {}


    def __init__(self, primary_fields_only=False, excluded=None, fields=None, primary_fields=None):
        self.fields = set(fields or self.fields)
        self.excluded = set(self.excluded) | set(excluded or ())
        self.primary_fields = set(primary_fields or self.primary_fields)
        self._primary_fields_only = primary_fields_only


    ### Querying

    def queryset(self, field_names):
        """
        Default query set for this Resource.

        Note that this isn't restricted to return a Django QuerySet. You could return
        whatever works for you as a "query set", just make sure you make good
        use of it in methods ``filter`` and ``get``.
        """
        if not self.model:
            raise NotImplementedError
        # TODO: be smarter when selecting related stuff
        return self.model.objects.select_related(depth=1)

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
        getter_name = 'get_%s' % field_name
        if hasattr(self, getter_name):
            meth = getattr(self, getter_name)
            value = meth(obj)
        else:
            value = getattr(obj, field_name)
        return value


    def _get_fields_values(self, obj, field_names):
        values = {}
        for field_name in field_names:
            values[field_name] = self._get_field_value(obj, field_name)
        return values


    def _get_robject(self, name, obj, field_names):
        if name is not None:
            name = force_unicode(name)
        ro = RObject(name)
        no_deep_fnames = set(x.split('.',1)[0] for x in field_names)
        for k,v in self._get_fields_values(obj, no_deep_fnames).iteritems():
            k = force_unicode(k)
            try:
                ro[k] = v
            except TypeError:
                restsource = self.relations[k]
                rdfn = set(restsource._default_field_names()) \
                     | set(x.split('.',1)[1] for x in field_names
                           if x.startswith(k+'.'))
                if isinstance(v, models.Manager):
                    # Reverse FK or Reverse M2M
                    ro[k] = restsource.dump_collection(v.all(), rdfn, named=False)
                elif isinstance(v, models.Model):
                    ro[k] = restsource.dump_single(v, rdfn, named=False)
        ro.special_keys = tuple(set(ro.keys()) & self.primary_fields)
        return ro

    ### Dumping Restsources

    def dump_single(self, obj, field_names, named=True):
        name = self.name if named else None
        return self._get_robject(name, obj, field_names)

    def dump_collection(self, objs, field_names, named=True):
        name = self.name_plural if named else None
        return RObjectList(name, [self.dump_single(x, field_names) for x in objs])

    def _default_field_names(self):
        field_names = self.primary_fields
        if not self._primary_fields_only:
            field_names = field_names | self.fields
        return field_names - self.excluded

    def _requested_field_names(self, options, request):
        field_names = self._default_field_names()
        fnq = request.REQUEST.get(options['field_names_qparam'], '').strip()
        if fnq:
            fns = set(x for x in (y.strip() for y in fnq.split(',')) if x)
            field_names  = set(x for x in fns if x[0].isalpha()) or field_names
            field_names |= set(x[1:] for x in fns if x[0] == '+')
            field_names -= set(x[1:] for x in fns if x[0] == '-')
            field_names &= self.fields
        return field_names | self.primary_fields

    ### HTTP requests handling
    def GET(self, options, request, params):
        field_names = self._requested_field_names(options, request)
        if options['single']:
            obj = self.get(self.queryset(field_names), request, **params)
            return Restponse(status=RESTPONSE_STATUS.OK, http_status=200,
                             payload=self.dump_single(obj, field_names))
        objs = self.filter(self.queryset(field_names), request, **params)
        if options['paginate_by']:
            return self._get_paginated_restponse(objs, field_names, options, request, params)
        return Restponse(status=RESTPONSE_STATUS.OK, http_status=200,
                         payload=self.dump_collection(objs, field_names))


    def POST(self, options, request, params):
        raise NotImplementedError

    def PUT(self, options, request, params):
        raise NotImplementedError

    def DELETE(self, options, request, params):
        raise NotImplementedError


    # Utils

    def _get_paginated_restponse(self, objs, field_names, options, request, params):
        assert request.method == 'GET', u"Paginating %s request not supported." % request.method
        page_qparam = options['page_qparam']
        paginate_by_qparam = options['paginate_by_qparam']
        try:
            g = lambda qparam,default: params.get(qparam, request.REQUEST.get(qparam, default))

            # page_num: look first in path info, then in query string, then default to 1
            page_num = int(g(page_qparam, 1))
            if page_num < 1:
                raise ValueError(u'page: %d' % page_nume)

            # paginate_by: if allowed, look first in path info, then in query string, otherwise use the default.
            if options['paginate_by'] is None:
                paginate_by = options['paginate_by']
            else:
                paginate_by = int(g(paginate_by_qparam, options['paginate_by']))
                if paginate_by < 1 or (options['paginate_by_max'] is not None and
                                       paginate_by >= options['paginate_by_max']):
                    raise ValueError(u'paginate_by: %d' % paginate_by)
            paginator = Paginator(objs, paginate_by, allow_empty_first_page=True)
            page = paginator.page(page_num)
        except (ValueError, InvalidPage):
            return Restponse(status=RESTPONSE_STATUS.ERROR_BAD_REQUEST,
                             info=u"Invalid page.", http_status=400)
        restponse = Restponse(status=RESTPONSE_STATUS.OK, http_status=200,
                              payload=self.dump_collection(page.object_list, field_names))

        ## Link headers
        qd = request.GET.copy()
        if paginate_by is not None:
            qd[paginate_by_qparam] = paginate_by

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

