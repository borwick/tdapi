import copy
import random
import string

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

    def all(self, data=None):
        all_records = []
        all_records += self.active(data)
        all_records += self.inactive(data)
        return all_records

    def active(self, data=None):
        # hard coded 1,000,000 as the max results
        data = self._copy_or_create(data,
                                    {'IsActive': True,
                                     'MaxResults': 1000000,
                                     })
        return self.search(data)

    def inactive(self, data=None):
        data = self._copy_or_create(data,
                                    {'IsActive': False,
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

    def userlist(self, active=None, employee=None, user_type=None):
        userlist_url = 'people/userlist?'

        # build the variables to pass to the GET
        userlist_vars = []
        if active is True:
            userlist_vars.append('isActive=True')
        elif active is False:
            userlist_vars.append('isActive=False')
        if employee is True:
            userlist_vars.append('isEmployee=True')
        elif employee is False:
            userlist_vars.append('isEmployee=False')
        if user_type is not None:
            userlist_vars.append('userType={}'.format(user_type))
        userlist_url += '&'.join(userlist_vars)

        return [TDPerson(td_struct)
                for td_struct
                in tdapi.TD_CONNECTION.json_request_roller(
                    method='get',
                    url_stem=userlist_url)]


class TDPerson(tdapi.obj.TDObject):
    def __init__(self, *args, **kwargs):
        super(TDPerson, self).__init__(*args, **kwargs)
        self._single_queried = False

    def __eq__(self, otro):
        return self.person_id() == otro.person_id()

    def __ne__(self, otro):
        return not self == otro

    def __hash__(self):
        # Needed for set operations
        return hash(self.person_id())

    def __str__(self):
        return self.get('FullName')

    def person_id(self):
        return self.get('UID')

    def person_url(self):
        return 'people/{}'.format(self.person_id())

    def _ensure_single_query(self):
        if self._single_queried is False:
            self.td_struct = tdapi.TD_CONNECTION.json_request(
                method='get',
                url_stem=self.person_url()
                )
            self._single_queried = True

    def import_string(self):
        return '{} <{}>'.format(self.get('FullName').encode('utf-8'), self.get('AlertEmail'))

    def add_group_by_id(self,
                        group_id,
                        isPrimary=False,
                        isNotified=True,
                        isManager=False,
    ):
        # does not currently support the optional arguments
        add_group_uri = self.person_url() + '/groups/{}'.format(group_id) + \
                        '?isPrimary={}'.format(isPrimary) + \
                        '&isNotified={}'.format(isNotified) + \
                        '&isManager={}'.format(isManager)
        
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

    def is_active(self):
        return self.get('IsActive') == True

    def update(self, update_data):
        # don't mess with the original data. copy into the update all
        # existing data. TODO consider purging cache and re-calling
        # query before doing this update.
        update_data = copy.deepcopy(update_data)
        self._ensure_single_query() # Make sure we have all attributes populated

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

    @classmethod
    def new(cls, update_data):
        update_data = copy.deepcopy(update_data)
        if 'TypeID' not in update_data:
            update_data['TypeID'] = 1 # User
        if 'UserName' not in update_data:
            update_data['UserName'] = update_data['AuthenticationUserName']
        if 'Password' not in update_data:
            random_password = ''.join(random.choice(string.ascii_uppercase + string.digits)
                                      for _ in range(20))
            update_data['Password'] = random_password
        if 'AlertEmail' not in update_data:
            update_data['AlertEmail'] = update_data['PrimaryEmail']

        tdapi.TD_CONNECTION.request(method='post',
                                    url_stem='people',
                                    data=update_data)


tdapi.obj.relate_cls_to_manager(TDPerson, TDPersonManager)

