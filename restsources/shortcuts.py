# -*- coding: utf8 -*-

from .restsource_value import RestsourceValue, Object, ObjectCollection


def payload_from_form_errors(form_errors):
    ferrors = []
    for field,field_errors in form_errors.iteritems():
        if field == '__all__':
            for fe in field_errors:
                rv = Object(u'error', {
                    RestsourceValue.get_for_value(u'info'): RestsourceValue.get_for_value(fe)
                })
                ferrors.append(rv)
        else:
            for fe in field_errors:
                rv = Object(u'error', {
                    RestsourceValue.get_for_value(u'field'): RestsourceValue.get_for_value(field),
                    RestsourceValue.get_for_value(u'info'): RestsourceValue.get_for_value(fe)
                }, ['field'])
                ferrors.append(rv)
    return ObjectCollection(u'errors', ferrors)
