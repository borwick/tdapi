import copy
import random
import string

import tdapi
import tdapi.obj
import tdapi.person


class TDGroupManager(tdapi.obj.TDObjectManager):
    def _copy_or_create(self, data, data_to_merge=None):
        if data is None:
            new_data = {}
        else:
            new_data = copy.deepcopy(data)
        new_data.update(data_to_merge)
        return new_data

    def search(self, data):
        return [self.object_class(td_struct)
                for td_struct
                in tdapi.TD_CONNECTION.json_request_roller(
                    method='post',
                    url_stem='groups/search',
                    data=data,
                )]

    def all(self, data=None):
        all_records = []
        all_records += self.active(data)
        all_records += self.inactive(data)
        return all_records

    def active(self, data=None):
        # hard coded 1,000,000 as the max results
        data = self._copy_or_create(data,
                                    {'IsActive': True,
                                     })
        return self.search(data)

    def inactive(self, data=None):
        data = self._copy_or_create(data,
                                    {'IsActive': False,
                                     })
        return self.search(data)


class TDGroupMember(tdapi.person.TDPerson):
    pass


class TDGroup(tdapi.obj.TDObject):
    def __str__(self):
        return self.get('Name')

    def __eq__(self, otro):
        return self.get('ID') == otro.get('ID')

    def __ne__(self, otro):
        return not self == otro

    def url(self):
        return 'groups/{}'.format(self.get('ID'))

    def members(self):
        members_url_stem = '{}/members'.format(self.url())
        return [TDGroupMember(td_struct)
                for td_struct
                in tdapi.TD_CONNECTION.json_request_roller(
                    method='get',
                    url_stem=members_url_stem,
                    )]

    def update(self, update_data):
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

        tdapi.TD_CONNECTION.request(method='put',
                                    url_stem=self.url(),
                                    data=update_data)
        
    @classmethod
    def new(cls, update_data):
        update_data = copy.deepcopy(update_data)
        tdapi.TD_CONNECTION.request(method='post',
                                    url_stem='groups',
                                    data=update_data)


tdapi.obj.relate_cls_to_manager(TDGroup, TDGroupManager)

