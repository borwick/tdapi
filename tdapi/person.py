import copy

import tdapi
import tdapi.obj


class TDPersonManager(tdapi.obj.TDObjectManager):
    def _copy_or_create(self, data, data_to_merge=None):
        if data is None:
            new_data = {}
        else:
            new_data = copy.deepcopy(data)
        new_data.update(data_to_merge)
        return new_data

    def search(self, data):
        return [TDPerson(td_struct)
                for td_struct
                in tdapi.TD_CONNECTION.json_request_roller(
                    method='post',
                    url_stem='people/search',
                    data=data,
                )]

    def active(self, data=None):
        data = self._copy_or_create(data,
                                    {'IsActive': True,
                                     })
        return self.search(data)

    def get(self, uid):
        user_url_stem = 'people/{}'.format(uid)
        td_struct = tdapi.TD_CONNECTION.json_request_roller(
            method='get',
            url_stem=user_url_stem)
        assert len(td_struct) == 1
        return self.object_class(td_struct[0])


class TDPerson(tdapi.obj.TDObject):
    def __str__(self):
        return self.get('FullName')

    def import_string(self):
        return '{} <{}>'.format(self.get('FullName').encode('utf-8'), self.get('AlertEmail'))

    def add_group_by_id(self, group_id):
        # does not currently support the optional arguments
        add_group_uri = 'people/{}/groups/{}'.format(self.get('UID'), group_id)
        tdapi.TD_CONNECTION.request(method='put',
                                    url_stem=add_group_uri)

tdapi.obj.relate_cls_to_manager(TDPerson, TDPersonManager)
