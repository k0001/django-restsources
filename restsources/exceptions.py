# -*- coding: utf8 -*-

__all__ = 'ResourceDoesNotExist', 'MultipleResourcesExist'


class ResourceDoesNotExist(Exception):
    pass

class MultipleResourcesExist(Exception):
    pass

