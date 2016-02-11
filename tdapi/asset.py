import copy

import api
import api.obj
from api.cmdb import TDConfigurationItem

from django.conf import settings


class TDProductTypeQuerySet(api.obj.TDQuerySet):
    pass


class TDProductTypeManager(api.obj.TDObjectManager):
    pass


class TDProductType(api.obj.TDObject):
    pass

api.obj.relate_cls_to_manager(TDProductType, TDProductTypeManager)


class TDResourceItemQuerySet(api.obj.TDQuerySet):
    def users(self):
        return TDResourceItemQuerySet([x for x in self.qs
                                       if x.td_struct['ItemRole'] == 'Person'])


class TDResourceItemManager(api.obj.TDObjectManager):
    pass


class TDResourceItem(api.obj.TDObject):
    pass

api.obj.relate_cls_to_manager(TDResourceItem, TDResourceItemManager)


class TDProductModelQuerySet(api.obj.TDQuerySet):
    pass


class TDProductModelManager(api.obj.TDObjectManager):
    def all(self):
        return TDProductModelQuerySet(
            [self.object_class(model)
                for model in settings.TD_CONNECTION.json_request_roller(
                        method='get',
                        url_stem='assets/models')]
            )

    def by_product_types(self, product_types):
        # FIXME this doesn't recurse through these types, because the
        # API doesn't have a way to do this. e.g. will find stuff uner
        # the listed type but not the type's sub-types.
        if len(product_types) == 0:
            raise api.TDException("No product types passed")

        # TODO make this work when `product_types` are actual
        # TDProductType objects.
        return [model for model in self.all()
                if model['ProductTypeName'] in product_types]


class TDProductModel(api.obj.TDObject):
    pass

api.obj.relate_cls_to_manager(TDProductModel, TDProductModelManager)


class TDAssetQuerySet(api.obj.TDQuerySet):
    def by_location_and_room(self):
        sorted_qs = sorted(self.qs,
                           key=lambda asset: asset.location_and_room_string())
        return TDAssetQuerySet(sorted_qs)


class TDAssetManager(api.obj.TDObjectManager):
    def search(self, data):
        """
        Only returns in-service assets.
        """
        # TODO: make this optional:
        data = copy.deepcopy(data)
        data['IsInService'] = True

        return TDAssetQuerySet(
            [TDAsset(td_struct)
                for td_struct
                in settings.TD_CONNECTION.json_request_roller(
                    method='post',
                    url_stem='assets/search',
                    data=data)]
            )

    def by_model(self, models):
        if len(models) == 0:
            raise api.TDException("No model passed")
        model_ids = [model['ID'] for model in models]

        return self.search({'ProductModelIDs': model_ids})

    def by_product_types(self, product_types):
        if len(product_types) == 0:
            raise api.TDException("No product types passed")

        models = TDProductModel.objects.by_product_types(product_types)
        return self.by_model(models)

    SERVER_PRODUCT_TYPES = ('Server',)

    def servers(self):
        return self.by_product_types(self.SERVER_PRODUCT_TYPES)

    LICENSE_PRODUCT_TYPES = ('Server-side license', 'Client-side license',)

    def licenses(self):
        return self.by_product_types(self.LICENSE_PRODUCT_TYPES)


class TDAsset(api.obj.TDObject):
    def __init__(self, *args, **kwargs):
        super(TDAsset, self).__init__(*args, **kwargs)
        # _single_queried represents, have we queried for this
        # specific asset vs. a group of assets?
        #
        # TODO set this appropriately
        self._single_queried = False

    def single_query_get(self, attr):
        """
        TeamDynamix won't pull all data for an asset unless you query the
        asset by itself. Use this method when you need to query data
        that only shows up when you query the asset by itself.
        """
        # If the struct has the value, then just use it.
        cached_attr_val = self.get(attr)
        if cached_attr_val:
            return cached_attr_val

        # If we haven't yet tried to query the asset, try querying it.
        if self._single_queried is False:
            self.td_struct = settings.TD_CONNECTION.json_request(
                method='get',
                url_stem=self.asset_url()
                )
            self._single_queried = True

        return self.get(attr)

    def attribute_get(self, attr):
        """
        Custom attributes are returned as a weird data structure. This
        basically ignores most of the data structure. You pass the
        attribute to get, and you get back the 'Value' from the
        attribute structure.
        """
        attributes_struct = self.single_query_get('Attributes')
        attribute_struct = [x for x in attributes_struct
                            if x['Name'] == attr]
        if len(attribute_struct) > 1:
            raise api.TDException("Too many attributes with name {}".format(attr))
        elif len(attribute_struct) == 0:
            return
        else:
            return attribute_struct[0]['Value']

    def name(self):
        return self.attribute_get('Name')

    def serial(self):
        return self.td_struct['SerialNumber']

    def tag(self):
        return self.td_struct['Tag']

    def __unicode__(self):
        name=self.name()
        if name is None:
            name='[Unnamed]'
        return "{} ({} / {})".format(name, self.serial(), self.tag())

    __str__ = __unicode__

    def ci(self):
        return TDConfigurationItem.objects.get(self.cmdb_id())

    def cmdb_id(self):
        return self.td_struct['ConfigurationItemID']

    def cmdb_url(self):
        return 'cmdb/{}'.format(self.cmdb_id())

    def related_cis(self):
        return self.ci().related_items()

    related_assets = related_cis

    def asset_id(self):
        return self.td_struct['ID']

    def asset_url(self):
        return 'assets/{}'.format(self.asset_id())

    def server_side_apps(self):
        return self.ci().related_items('Server-side application')

    def virtual_servers(self):
        return self.ci().related_items('Virtual server')

    def location(self):
        location_id = self.get('LocationID')
        if location_id:
            return TDLocation.objects.get(location_id)
        else:
            return None

    def room(self):
        room_id = self.get('LocationRoomID')
        if room_id:
            return self.location().get_room(room_id)
        else:
            return None

    def location_and_room_string(self):
        location = self.location()
        room = self.room()
        return "{}: {}".format(location, room)

    def related_resources(self):
        return TDResourceItemQuerySet(
            [TDResourceItem(td_struct)
                for td_struct
                in settings.TD_CONNECTION.json_request_roller(
                    method='get',
                    url_stem='assets/{}/users'.format(self.td_struct['ID']))
            ])

    def related_users(self):
        return self.related_resources().users()

api.obj.relate_cls_to_manager(TDAsset, TDAssetManager)


class TDLocationQuerySet(api.obj.TDQuerySet):
    pass


class TDLocationManager(api.obj.TDObjectManager):
    def get(self, location_id):
        room_url_stem = 'locations/{}'.format(location_id)
        td_struct = settings.TD_CONNECTION.json_request_roller(
            method='get',
            url_stem=room_url_stem)
        assert len(td_struct) == 1
        return self.object_class(td_struct[0])


class TDLocation(api.obj.TDObject):
    def __eq__(self, otro):
        if otro is None:
            return False
        return self.get('ID') == otro.get('ID')

    def get_room(self, room_id):
        rooms = self.get('Rooms')
        matching_rooms = [room for room in rooms
                          if room['ID'] == room_id]
        if len(matching_rooms) < 1:
            raise api.TDException("Room ID {} not found in location ID {}".format(
                room_id,
                self.td_struct['ID']))
        elif len(matching_rooms) > 1:
            assert "Too many matching rooms"
        else:
            return TDRoom(matching_rooms[0])

    def __unicode__(self):
        return self.get('Name')

    __str__ = __unicode__


api.obj.relate_cls_to_manager(TDLocation, TDLocationManager)


class TDRoomQuerySet(api.obj.TDQuerySet):
    pass


class TDRoomManager(api.obj.TDObjectManager):
    pass


class TDRoom(api.obj.TDObject):
    def __eq__(self, otro):
        if otro is None:
            return False
        return self.get('ID') == otro.get('ID')

    def __unicode__(self):
        return self.get('Name')

    __str__ = __unicode__

api.obj.relate_cls_to_manager(TDRoom, TDRoomManager)
