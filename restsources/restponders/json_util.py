from __future__ import absolute_import

import sys

__all__ = 'json'


MODULES = (('czjson',                  'dumps',    'loads'),
           ('cjson',                   'encode',   'decode'),
           ('simplejson',              'dumps',    'loads'),
           ('json',                    'dumps',    'loads'),
           ('django.utils.simplejson', 'dumps',    'loads'))


class JSON(object):
    def __init__(self, mod, dumps, loads):
        self.mod = mod
        self.dumps = lambda obj: dumps(obj)
        self.loads = lambda s: loads(s)


for m, d, l in MODULES:
    try:
        __import__(m)
        mod = sys.modules[m]
        json = JSON(mod, getattr(mod, d), getattr(mod, l))
        break
    except ImportError:
        pass
else:
    raise ImportError(u"No JSON module available, install one of: %s" \
                            % u", ".join(x[0] for x in _modules))


