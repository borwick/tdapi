import copy
import random
import string

import tdapi
import tdapi.obj


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



class TDGroup(tdapi.obj.TDObject):
    def __str__(self):
        return self.get('Name')


tdapi.obj.relate_cls_to_manager(TDGroup, TDGroupManager)

