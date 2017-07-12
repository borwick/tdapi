import copy

import tdapi
import tdapi.obj
from tdapi.cmdb import TDConfigurationItem


class TDProductTypeQuerySet(tdapi.obj.TDQuerySet):
    pass


class TDProductTypeManager(tdapi.obj.TDObjectManager):
    pass


class TDProductType(tdapi.obj.TDObject):
    pass

tdapi.obj.relate_cls_to_manager(TDProductType, TDProductTypeManager)


class TDResourceItemQuerySet(tdapi.obj.TDQuerySet):
    def users(self):
        return TDResourceItemQuerySet([x for x in self.qs
                                       if x.td_struct['ItemRole'] == 'Person'])


class TDResourceItemManager(tdapi.obj.TDObjectManager):
    pass


class TDResourceItem(tdapi.obj.TDObject):
    pass

tdapi.obj.relate_cls_to_manager(TDResourceItem, TDResourceItemManager)


class TDProductModelQuerySet(tdapi.obj.TDQuerySet):
    pass


class TDProductModelManager(tdapi.obj.TDObjectManager):
    def all(self):
        return TDProductModelQuerySet(
            [self.object_class(model)
                for model in tdapi.TD_CONNECTION.json_request_roller(
                        method='get',
                        url_stem='assets/models')]
            )

    def by_product_types(self, product_types):
        # FIXME this doesn't recurse through these types, because the
        # TDAPI doesn't have a way to do this. e.g. will find stuff uner
        # the listed type but not the type's sub-types.
        if len(product_types) == 0:
            raise tdapi.TDException("No product types passed")

        # TODO make this work when `product_types` are actual
        # TDProductType objects.
        return [model for model in self.all()
                if model['ProductTypeName'] in product_types]


class TDProductModel(tdapi.obj.TDObject):
    pass

tdapi.obj.relate_cls_to_manager(TDProductModel, TDProductModelManager)


class TDAssetQuerySet(tdapi.obj.TDQuerySet):
    def by_location_and_room(self):
        sorted_qs = sorted(self.qs,
                           key=lambda asset: asset.location_and_room_string())
        return TDAssetQuerySet(sorted_qs)


class TDAssetManager(tdapi.obj.TDObjectManager):
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
                in tdapi.TD_CONNECTION.json_request_roller(
                    method='post',
                    url_stem='assets/search',
                    data=data)]
            )

    def by_model(self, models):
        if len(models) == 0:
            raise tdapi.TDException("No model passed")
        model_ids = [model['ID'] for model in models]

        return self.search({'ProductModelIDs': model_ids})

    def by_product_types(self, product_types):
        if len(product_types) == 0:
            raise tdapi.TDException("No product types passed")

        models = TDProductModel.objects.by_product_types(product_types)
        return self.by_model(models)

    SERVER_PRODUCT_TYPES = ('Server',)

    def servers(self):
        return self.by_product_types(self.SERVER_PRODUCT_TYPES)

    LICENSE_PRODUCT_TYPES = ('Server-side license', 'Client-side license',)

    def licenses(self):
        return self.by_product_types(self.LICENSE_PRODUCT_TYPES)

    def all(self):
        return self.search(data={})


class TDAsset(tdapi.obj.TDObject):
    def __init__(self, *args, **kwargs):
        super(TDAsset, self).__init__(*args, **kwargs)
        self._single_queried = False

    def _ensure_single_query(self):
        if self._single_queried is False:
            self.td_struct = tdapi.TD_CONNECTION.json_request(
                method='get',
                url_stem=self.asset_url()
                )
            self._single_queried = True

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
            raise tdapi.TDException("Too many attributes with name {}".format(attr))
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
                in tdapi.TD_CONNECTION.json_request_roller(
                    method='get',
                    url_stem='assets/{}/users'.format(self.td_struct['ID']))
            ])

    def related_users(self):
        return self.related_resources().users()

    def update(self, update_data):
        self._ensure_single_query()
        update_data = copy.deepcopy(update_data)

        seen_all = True
        for (update_key, update_val) in update_data.items():
            if self.get(update_key) != update_val:
                seen_all = False
                break
        if seen_all == True:
            return

        for orig_attr in self.td_struct.keys():
            if orig_attr not in update_data:
                update_data[orig_attr] = self.td_struct[orig_attr]

        tdapi.TD_CONNECTION.request(method='post',
                                    url_stem=self.asset_url(),
                                    data=update_data)


tdapi.obj.relate_cls_to_manager(TDAsset, TDAssetManager)


class TDLocationQuerySet(tdapi.obj.TDQuerySet):
    pass


class TDLocationManager(tdapi.obj.TDObjectManager):
    def _copy_or_create(self, data, data_to_merge=None):
        if data is None:
            new_data = {}
        else:
            new_data = copy.deepcopy(data)
        new_data.update(data_to_merge)
        return new_data


    def get(self, location_id):
        room_url_stem = 'locations/{}'.format(location_id)
        td_struct = tdapi.TD_CONNECTION.json_request_roller(
            method='get',
            url_stem=room_url_stem)
        assert len(td_struct) == 1
        return self.object_class(td_struct[0])

    def search(self, data):
        return [self.object_class(td_struct)
                for td_struct
                in tdapi.TD_CONNECTION.json_request_roller(
                    method='post',
                    url_stem='locations/search',
                    data=data)]

    def active(self, data=None):
        data = self._copy_or_create(data,
                                    {'IsActive': True,
                                     })
        return self.search(data)

    def inactive(self, data=None):
        data = self._copy_or_create(data,
                                    {'IsActive': False,
                                     })
        return self.search(data)

    def all(self, data=None):
        all_records = []
        all_records += self.active(data)
        all_records += self.inactive(data)
        return all_records

class TDLocation(tdapi.obj.TDObject):
    def __init__(self, *args, **kwargs):
        super(TDLocation, self).__init__(*args, **kwargs)
        self._single_queried = False
        self.TDRoom = TDRoomFactory(location=self)

    def location_id(self):
        return self.get('ID')

    def location_url(self):
        return 'locations/{}'.format(self.location_id())

    def __eq__(self, otro):
        if otro is None:
            return False
        return self.get('ID') == otro.get('ID')

    def _ensure_single_query(self):
        if self._single_queried is False:
            self.td_struct = tdapi.TD_CONNECTION.json_request(
                method='get',
                url_stem=self.location_url()
                )
            self._single_queried = True

    def rooms(self):
        return [self.TDRoom(td_struct)
                for td_struct
                in self.single_query_get('Rooms')]

    def get_room(self, room_id):
        rooms = self.get('Rooms')
        matching_rooms = [room for room in rooms
                          if room['ID'] == room_id]
        if len(matching_rooms) < 1:
            raise tdapi.TDException("Room ID {} not found in location ID {}".format(
                room_id,
                self.td_struct['ID']))
        elif len(matching_rooms) > 1:
            assert "Too many matching rooms"
        else:
            return self.TDRoom(matching_rooms[0])

    def __unicode__(self):
        return self.get('Name')

    __str__ = __unicode__


tdapi.obj.relate_cls_to_manager(TDLocation, TDLocationManager)


class TDRoomQuerySet(tdapi.obj.TDQuerySet):
    pass


class TDBaseRoomManager(tdapi.obj.TDObjectManager):
    LOCATION = None


class TDBaseRoom(tdapi.obj.TDObject):
    LOCATION = None

    def __eq__(self, otro):
        if otro is None:
            return False
        return self.get('ID') == otro.get('ID')

    @classmethod
    def location(cls):
        return cls.LOCATION

    def __unicode__(self):
        return self.get('Name')

    def room_id(self):
        return self.get('ID')
    
    def url(self):
        return self.location().location_url() + \
            '/rooms/{}'.format(self.room_id())

    def update(self, update_data):
        # don't mess with the original data. copy into the update all
        # existing data. TODO consider purging cache and re-calling
        # query before doing this update.
        update_data = copy.deepcopy(update_data)
        # TODO should this do a single query get?
        
        # short circuit to make sure update_data is not already set
        seen_all = True
        for (update_key, update_val) in update_data.items():
            if self.get(update_key) != update_val:
                seen_all = False
                break
        if seen_all == True:
            return
        
        for orig_attr in self.td_struct.keys():
            if orig_attr not in update_data:
                update_data[orig_attr] = self.td_struct[orig_attr]

        tdapi.TD_CONNECTION.request(method='put',
                                    url_stem=self.url(),
                                    data=update_data)

    __str__ = __unicode__

def TDRoomFactory(location):
    """
    Created a room factory--each location creates a room class.
    """
    class TDRoomManager(TDBaseRoomManager):
        LOCATION = location

    class TDRoom(TDBaseRoom):
        LOCATION = location

    tdapi.obj.relate_cls_to_manager(TDRoom, TDRoomManager)
    return TDRoom
