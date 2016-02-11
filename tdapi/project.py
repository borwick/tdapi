import copy
import time
import iso8601
import urlparse

import api.obj

from django.conf import settings


class TDProjectQuerySet(api.obj.TDQuerySet):
    def by_end_date(self):
        end_date_lookup = lambda x: x.td_struct['EndDate']
        self.qs.sort(key=end_date_lookup)
        return self


class TDProjectManager(api.obj.TDObjectManager):
    def search(self, data):
        return TDProjectQuerySet(
            [self.object_class(project)
             for project in settings.TD_CONNECTION.json_request_roller(
                     method='post',
                     url_stem='projects/search',
                     data=data,
             )])

    def _copy_or_create(self, data, data_to_merge=None):
        if data is None:
            new_data = {}
        else:
            new_data = copy.deepcopy(data)
        new_data.update(data_to_merge)
        return new_data

    def _today_date(self):
        """
        Returns today's date. I think this uses the active timezone.
        """
        return time.strftime('%Y-%m-%d')

    def active(self, data=None):
        data = self._copy_or_create(data,
                                    {'IsPrivate': False,
                                     'IsActive': True,
                                     })
        return self.search(data)

    def current(self, data=None):
        data = self._copy_or_create(data,
                                    {'Starts': self._today_date(),
                                     'StartsOperator': '<',
                                    })
        return self.active(data)

    def future(self, data=None):
        data = self._copy_or_create(data,
                                    {'Starts': self._today_date(),
                                     'StartsOperator': '>',
                                     })
        return self.active(data)


class TDProject(api.obj.TDObject):
    def __str__(self):
        return self.get('Name')

    def health(self):
        """
        Walks from the TD struct into health strings. This is reverse
        engineered.
        """
        return {3: 'Red',
                2: 'Yellow',
                1: 'Green',
                0: 'Unknown',
                4: 'On Hold'
                }[self.td_struct['Health']]

    def start_date(self):
        return iso8601.parse_date(self.td_struct['StartDate']).strftime('%Y-%m-%d')

    def end_date(self):
        return iso8601.parse_date(self.td_struct['EndDate']).strftime('%Y-%m-%d')

    def td_url(self):
        project_details_url = urlparse.urljoin(settings.TD_CLIENT_URL,
                                               'Projects/Details/')
        return '{}?TID={}'.format(project_details_url, self.td_struct['ID'])

api.obj.relate_cls_to_manager(TDProject, TDProjectManager)
