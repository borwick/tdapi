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
        # hard coded 1,000,000 as the max results
        data = self._copy_or_create(data,
                                    {'IsActive': True,
                                     'MaxResults': 1000000,
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
    def __init__(self, *args, **kwargs):
        super(TDPerson, self).__init__(*args, **kwargs)
        self._single_queried = False
        
    def __str__(self):
        return self.get('FullName')

    def person_id(self):
        return self.get('UID')

    def person_url(self):
        return 'people/{}'.format(self.person_id())

    def single_query_get(self, attr):
        # modeled off off TDAsset.single_query_get
        cached_attr_val = self.get(attr)
        if cached_attr_val:
            return cached_attr_val

        if self._single_queried is False:
            self.td_struct = tdapi.TD_CONNECTION.json_request(
                method='get',
                url_stem=self.person_url()
                )
            self._single_queried = True

        return self.get(attr)

    def import_string(self):
        return '{} <{}>'.format(self.get('FullName').encode('utf-8'), self.get('AlertEmail'))

    def add_group_by_id(self, group_id):
        # does not currently support the optional arguments
        add_group_uri = self.person_url() + '/groups/{}'.format(group_id)
        tdapi.TD_CONNECTION.request(method='put',
                                    url_stem=add_group_uri)

    def del_group_by_id(self, group_id):
        del_group_uri = self.person_url() + '/groups/{}'.format(group_id)
        tdapi.TD_CONNECTION.request(method='delete',
                                    url_stem=del_group_uri)

    def set_active(self, active):
        activate_uri =  self.person_url() + '/isactive?status={}'.format(active)
        tdapi.TD_CONNECTION.request(method='put',
                                    url_stem=activate_uri)

    def activate(self):
        return self.set_active(True)

    def deactivate(self):
        return self.set_active(False)

    def update(self, update_data):
        # don't mess with the original data. copy into the update all
        # existing data. TODO consider purging cache and re-calling
        # query before doing this update.
        update_data = copy.deepcopy(update_data)
        for orig_attr in self.td_struct.keys():
            if orig_attr not in update_data:
                update_data[orig_attr] = self.td_struct[orig_attr]

        tdapi.TD_CONNECTION.request(method='post',
                                    url_stem=self.person_url(),
                                    data=update_data)

    def add_applications(self, app_list):
        all_apps = list(set(self.td_struct['Applications'] + app_list))
        return self.update({'Applications': all_apps})

    def del_applications(self, app_list):
        all_apps = [x for x in self.td_struct['Applications']
                    if x not in app_list]
        return self.update({'Applications': all_apps})

tdapi.obj.relate_cls_to_manager(TDPerson, TDPersonManager)
