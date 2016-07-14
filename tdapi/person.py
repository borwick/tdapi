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

    def del_group_by_id(self, group_id):
        del_group_uri = 'people/{}/groups/{}'.format(self.get('UID'), group_id)
        tdapi.TD_CONNECTION.request(method='delete',
                                    url_stem=del_group_uri)

    def set_active(self, active):
        activate_uri = 'people/{}/isactive?status={}'.format(self.get('UID'), active)
        tdapi.TD_CONNECTION.request(method='put',
                                    url_stem=activate_uri)

    def activate(self):
        return self.set_active(True)

    def deactivate(self):
        return self.set_active(False)

    def update(self, update_data):
        update_uri = 'people/{}'.format(self.get('UID'))

        # don't mess with the original data. copy into the update all
        # existing data. TODO consider purging cache and re-calling
        # query before doing this update.
        update_data = copy.deepcopy(update_data)
        for orig_attr in self.td_struct.keys():
            if orig_attr not in update_data:
                update_data[orig_attr] = self.td_struct[orig_attr]

        tdapi.TD_CONNECTION.request(method='post',
                                    url_stem=update_uri,
                                    data=update_data)

    def add_applications(self, app_list):
        all_apps = list(set(self.td_struct['Applications'] + app_list))
        return self.update({'Applications': all_apps})

    def del_applications(self, app_list):
        all_apps = [x for x in self.td_struct['Applications']
                    if x not in app_list]
        return self.update({'Applications': all_apps})

tdapi.obj.relate_cls_to_manager(TDPerson, TDPersonManager)
