import copy

from django.conf import settings

import api.obj


class TDRelationshipTypeQuerySet(api.obj.TDQuerySet):
    pass


class TDRelationshipTypeManager(api.obj.TDObjectManager):
    def all(self):
        return TDRelationshipTypeQuerySet(
            [self.object_class(td_struct)
                for td_struct
                in settings.TD_CONNECTION.json_request(
                    method='get',
                    url_stem='cmdb/relationshiptypes')]
            )

    def by_name(self, name):
        named_type = [x for x in self.all() if x.get('Description') == name]
        assert len(named_type) == 1
        return named_type[0]


class TDRelationshipType(api.obj.TDObject):
    def id(self):
        return self.get('ID')

api.obj.relate_cls_to_manager(TDRelationshipType, TDRelationshipTypeManager)


class TDRelationshipQuerySet(api.obj.TDQuerySet):
    pass


class TDRelationshipManager(api.obj.TDObjectManager):
    pass


class TDRelationship(api.obj.TDObject):
    def child_id(self):
        return self.td_struct['ChildID']

    def child_type_name(self):
        return self.td_struct['ChildTypeName']

    def child(self):
        return TDConfigurationItem.objects.get(self.child_id())

    def parent_id(self):
        return self.td_struct['ParentID']

    def parent_type_name(self):
        return self.td_struct['ParentTypeName']

    def parent(self):
        return TDConfigurationItem.objects.get(self.parent_id())

api.obj.relate_cls_to_manager(TDRelationship, TDRelationshipManager)


class TDConfigurationTypeQuerySet(api.obj.TDQuerySet):
    pass


class TDConfigurationTypeManager(api.obj.TDObjectManager):
    def all(self):
        return TDConfigurationTypeQuerySet(
            [self.object_class(td_struct)
                for td_struct
                in settings.TD_CONNECTION.json_request_roller(
                    method='get',
                    url_stem='cmdb/types')]
            )

    def by_type_names(self, type_names):
        return [x for x in self.all()
                if x['Name'] in type_names]


class TDConfigurationType(api.obj.TDObject):
    def name(self):
        return self.get('Name')

    def id(self):
        return self.get('ID')

api.obj.relate_cls_to_manager(TDConfigurationType, TDConfigurationTypeManager)


class TDConfigurationItemQuerySet(api.obj.TDQuerySet):
    pass


class TDConfigurationItemManager(api.obj.TDObjectManager):
    ci_types = None

    def _ci_type_ids(self):
        if self.ci_types:
            return [x.td_struct['ID']
                    for x
                    in TDConfigurationType.objects.by_type_names(self.ci_types)
                    ]

    def all(self):
        return self.search(data={})

    def get(self, cmdb_id):
        cmdb_url_stem = 'cmdb/{}'.format(cmdb_id)
        td_struct = settings.TD_CONNECTION.json_request_roller(
            method='get',
            url_stem=cmdb_url_stem)
        assert len(td_struct) == 1
        return self.object_class(td_struct[0])

    def search(self, data):
        if self.ci_types:
            data = copy.deepcopy(data)
            data['TypeIDs'] = self._ci_type_ids()

        return TDConfigurationItemQuerySet(
            [self.object_class(td_struct)
                for td_struct
                in settings.TD_CONNECTION.json_request_roller(
                    method='post',
                    url_stem='cmdb/search',
                    data=data)]
            )

    def by_types(self, types):
        ci_type_ids = [x.ID
                       for x in types]
        return self.search(data={'TypeIDs': ci_type_ids})


class TDConfigurationItem(api.obj.TDObject):
    def __init__(self, *args, **kwargs):
        super(TDConfigurationItem, self).__init__(*args, **kwargs)
        self._single_queried = False
        self._attributes = None

    def single_query_get(self, attr):
        cached_attr_val = self.get(attr)
        if cached_attr_val:
            return cached_attr_val

        if self._single_queried is False:
            self.td_struct = settings.TD_CONNECTION.json_request(
                method='get',
                url_stem=self.url(),
                )
            self._single_queried = True

        return self.get(attr)

    def name(self):
        return self.td_struct['Name']

    def __unicode__(self):
        return "{}".format(self.name())

    __str__ = __unicode__

    def id(self):
        return self.td_struct['ID']

    def url(self):
        return 'cmdb/{}'.format(self.id())

    def relationships(self):
        return [TDRelationship(td_struct)
                for td_struct
                in settings.TD_CONNECTION.json_request_roller(
                    method='get',
                    url_stem="{}/relationships".format(self.url()))]

    def related_items(self, type_names=None):
        """
        Returns CIs that are related to this CI.

        If `type_names` is specified then only CIs of the listed types
        are allowed. Pass as a tuple e.g.

            type_names['Server-side app', 'Server',]

        Note these are CI types not asset types.
        """
        related_cmdb_items = []
        for relationship in self.relationships():
            if relationship.child_id() == self.id():
                # look at parent
                if type_names is None or \
                   relationship.parent_type_name() in type_names:
                    related_cmdb_items.append(relationship.parent())
            else:
                if type_names is None or \
                   relationship.child_type_name() in type_names:
                    related_cmdb_items.append(relationship.child())

        return related_cmdb_items

    def attributes(self):
        # cached ?
        if self._attributes:
            return self._attributes

        # go get the Attributes value, which may or may not be in
        # td_struct already.
        raw_attributes = self.single_query_get('Attributes')

        # build the attributes that we're going to cache.
        attributes = {}
        for raw_attribute in raw_attributes:
            attribute_name = raw_attribute['Name']
            attribute_value = raw_attribute['ValueText']
            attributes[attribute_name] = attribute_value
        self._attributes = attributes

        # return the new, cached attributes
        return self._attributes

    def is_asset(self):
        type_name = self.single_query_get('TypeName')
        return type_name == 'Asset'

    def add_relationship(self, other_ci_id):
        # TODO this looks a bit ugly and probably needs to be redone.
        uses_relationship = TDRelationshipType.objects.by_name('Uses')
        add_url = self.url() + '/relationships?typeid={}&'.format(uses_relationship.id())
        add_url += 'otheritemid={}&'.format(other_ci_id)
        add_url += 'isparent=False'

        settings.TD_CONNECTION.json_request(method='put',
                                            url_stem=add_url)

    def attribute(self, attr_name):
        return self.attributes()[attr_name]

api.obj.relate_cls_to_manager(TDConfigurationItem,
                              TDConfigurationItemManager)


class TDServerSideAppManager(TDConfigurationItemManager):
    ci_types = ['Server-side application', ]


class TDServerSideApp(TDConfigurationItem):
    pass

api.obj.relate_cls_to_manager(TDServerSideApp,
                              TDServerSideAppManager)


class TDVirtualServerManager(TDConfigurationItemManager):
    ci_types = ['Virtual server', ]


class TDVirtualServer(TDConfigurationItem):
    pass

api.obj.relate_cls_to_manager(TDVirtualServer,
                              TDVirtualServerManager)
