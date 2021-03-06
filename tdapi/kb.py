import copy

import tdapi
import tdapi.obj


class TDKnowledgeArticleManager(tdapi.obj.TDObjectManager):
    def search(self, data):
        new_data = copy.deepcopy(data)
        if not new_data.has_key('ReturnCount'):
            new_data['ReturnCount'] = 100000
        return [self.object_class(obj)
                for obj in tdapi.TD_CONNECTION.json_request_roller(
                     method='post',
                     url_stem='knowledgebase/search',
                     data=new_data,
                        )]

    def all(self, data=None):
        if data is None:
            new_data = {}
        else:
            new_data = copy.deepcopy(data)
        new_data['Status'] = None
        return self.search(new_data)

    def approved(self, data=None):
        if data is None:
            new_data = {}
        else:
            new_data = copy.deepcopy(data)
        new_data['Status'] = 'Approved'
        return self.search(new_data)


class TDKnowledgeArticle(tdapi.obj.TDObject):
    def __init__(self, *args, **kwargs):
        # fix:
        super(TDKnowledgeArticle, self).__init__(*args, **kwargs)
        self._single_queried = False

    def __str__(self):
        return self.get('Subject')

    def _ensure_single_query(self):
        if self._single_queried is False:
            self.td_struct = tdapi.TD_CONNECTION.json_request(
                method='get',
                url_stem=self.url()
                )
            self._single_queried = True

    def url(self):
        return 'knowledgebase/{}'.format(self.get('ID'))

    # TODO move this into TDObject ?
    def update(self, update_data):
        update_data = copy.deepcopy(update_data)
        self._ensure_single_query()

        seen_all = True
        for (update_key, update_val) in update_data.items():
            if self.get(update_key) != update_val:
                seen_all = False
                break
        if seen_all == True:
            return

        for orig_attr in self.td_struct.keys():
            if orig_attr in ('Attachments'):
               pass
            elif orig_attr not in update_data:
                update_data[orig_attr] = self.td_struct[orig_attr]

        tdapi.TD_CONNECTION.request(method='put',
                                    url_stem=self.url(),
                                    data=update_data)


tdapi.obj.relate_cls_to_manager(TDKnowledgeArticle,
                                TDKnowledgeArticleManager
)
