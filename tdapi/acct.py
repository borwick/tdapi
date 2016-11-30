import copy

import tdapi
import tdapi.obj


class TDAcctDeptManager(tdapi.obj.TDObjectManager):
    def all(self):
        return [self.object_class(obj)
                for obj in tdapi.TD_CONNECTION.json_request_roller(
                        method='get',
                        url_stem='accounts',
                        )]


class TDAcctDept(tdapi.obj.TDObject):
    def __str__(self):
        return self.get('Name')

    def url(self):
        return 'accounts/{}'.format(self.get('ID'))

    # TODO move this into TDObject ?
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
                                    url_stem='accounts',
                                    data=update_data)

tdapi.obj.relate_cls_to_manager(TDAcctDept,
                                TDAcctDeptManager
)
