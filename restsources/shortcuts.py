# -*- coding: utf8 -*-

from .restsource import RObject, RObjectList


# TODO TEST

def payload_from_form_errors(form_errors):
    errors = RObjectList(u'errors')
    for field,field_errors in form_errors.iteritems():
        if field == '__all__':
            for fe in field_errors:
                errors.append(RObject(u'error', { u'info': fe }))
        else:
            for fe in field_errors:
                errors.append(RObject(u'error', { u'field': field, u'info': fe }, ['field']))
    return errors
