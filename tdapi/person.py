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


class TDPerson(tdapi.obj.TDObject):
    def __str__(self):
        return self.get('FullName')

tdapi.obj.relate_cls_to_manager(TDPerson, TDPersonManager)
