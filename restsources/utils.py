# -*- coding: utf8 -*-


# Code from Django REST interface
#   License: New BSD License
#   URL: http://code.google.com/p/django-rest-interface/
#   Contact: Andreas Stuhlmüller <andreas@stuhlmueller.info>
def load_put_and_files(request):
    """
    Populates request.PUT and request.FILES from
    request.raw_post_data. PUT and POST requests differ
    only in REQUEST_METHOD, not in the way data is encoded.
    Therefore we can use Django's POST data retrieval method
    for PUT.
    """
    if request.method == 'PUT':
        request.method = 'POST'
        request._load_post_and_files()
        request.method = 'PUT'
        request.PUT = request.POST
        del request._post

