#!/usr/bin/env python
# -*- coding: utf8 -*-

from setuptools import setup, find_packages

setup(
    name = "django-restsources",
    version = "0.1alpha5",
    packages = find_packages(),

    zip_safe = True,
    include_package_data = True,


    description = u"A Django framework for building REST APIs.",
    url = u"http://github.com/k0001/django-restsources",
    author = u"Renzo Carbonara",
    author_email = u"gnuk0001@gmail.com",
    license = u"BSD",
    keywords = "django rest api framework http web",


    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]

)

