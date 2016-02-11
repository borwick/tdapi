from django.conf import settings
"""
Foundational class for TD objects.
"""


class TDQuerySet(object):
    def __init__(self, data):
        self.qs = data

    def __iter__(self):
        for item in self.qs:
            yield item

    def __len__(self):
        return len(self.qs)


class TDObjectManager(object):
    """
    Modeled on Django's Model Manager. This is the parent class for
    TD search stuff.
    """
    object_class = None

    def json_request(self, *args, **kwargs):
        return settings.TD_CONNECTION.json_request(*args, **kwargs)


class TDObject(object):
    """
    Modeled on Django's Models. This is the parent class for TD
    objects.
    """
    objects = None

    def __init__(self, td_struct):
        self.td_struct = td_struct

    def __getitem__(self, key):
        return self.td_struct[key]

    def get(self, *args, **kwargs):
        return self.td_struct.get(*args, **kwargs)


def relate_cls_to_manager(cls, mgr):
    """
    This is a hack function to take a class and associate it with the
    manager.

    This exists because you can't refer to a class from within itself.

    Adds two relationships:

    cls.objects gets set to a new instance of mgr()

    mgr.object_class, conversely, gets set to the cls itself, so that
    the manager can instantiate new objects.
    """
    cls.objects = mgr()
    mgr.object_class = cls
