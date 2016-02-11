"""
TeamDynamix API.
"""
import json
import urlparse
import logging

import requests
import requests_cache

import api.asset
import api.cmdb

# cache requests:
requests_cache.install_cache(expire_after=60*15)


class TDException(Exception):
    """
    Any manner of TD error e.g. failed login.

    Returned for non-200 HTTP response codes.
    """
    pass


class TDAuthorizationException(Exception):
    """
    Returned for 401 unauthorized HTTP response code.
    """
    pass


class TDConnection(object):
    """
    This uses the TeamDynamix API:

        https://community.teamdynamix.com/Developers/REST/Default.aspx

    This class manages authentication and API requests. Instantiation
    requires a login.

    Typical use:

        conn = api.TDConnection(BEID='key-here',
                                WebServicesKey='key-here')
        conn.post_accounts_search(method='post',
                                  url_stem='accounts/search',
                                  data={'search': 'Test'})

    """
    URL_ROOT = 'https://api.teamdynamix.com/TDWebApi/api/'

    def __init__(self,
                 BEID,
                 WebServicesKey):
        """
        TODO this only uses the new superuser login option with BEID and
        WebServicesKey.
        """
        self.bearer_token = False            # This will be set in login()
        self.BEID = BEID
        self.WebServicesKey = WebServicesKey
        self.session = requests.Session()

        self.login()

    def _make_url(self, url_stem):
        """
        This uses urljoin to create the absolute URL.
        """
        return urlparse.urljoin(self.URL_ROOT, url_stem)

    def raw_request(self, method, url_stem, data=None, bearer_required=True):
        """
        This method POSTs to TeamDynamix.

        `data` will be converted to JSON.

        The `bearer_required` option is only set to false for logging
        in.
        """
        headers = {}
        headers['Content-Type'] = 'application/json'

        if method not in ('post', 'get', 'delete', 'put'):
            raise TDException("method {} not supported".format(method))

        if bearer_required:
            headers['Authorization'] = 'Bearer {}'.format(self.bearer_token)

        if data is not None:
            payload = json.dumps(data)
        else:
            payload = ''

        if method == 'post':
            logging.debug('POST to %s, data %s',
                          self._make_url(url_stem),
                          payload)
            resp = self.session.post(self._make_url(url_stem),
                                     data=payload,
                                     headers=headers,
                                 )
        elif method == 'get':
            logging.debug('GET to %s, data %s',
                          self._make_url(url_stem),
                          payload)
            resp = self.session.get(self._make_url(url_stem),
                                    data=payload,
                                    headers=headers,
                                 )
        elif method == 'delete':
            logging.debug('DELETE to %s, data %s',
                          self._make_url(url_stem),
                          payload)
            resp = self.session.delete(self._make_url(url_stem),
                                       data=payload,
                                       headers=headers,
                                   )
        elif method == 'put':
            logging.debug('PUT to %s, data %s',
                          self._make_url(url_stem),
                          payload)
            resp = self.session.put(self._make_url(url_stem),
                                       data=payload,
                                       headers=headers,
                                   )

        logging.debug('Response code: %s\nResponse: %s',
                      resp.status_code,
                      resp.text)

        if resp.status_code == 401:
            raise TDAuthorizationException("{} returned 401 status\n{}".format(
                url_stem, resp.text))
        elif resp.status_code not in [200, 201]:
            raise TDException("{} returned non-200 status ({})\n{}".format(
                url_stem, resp.status_code, resp.text))

        return resp

    def request(self, *args, **kwargs):
        """
        Calls raw_request. If TDAuthorizationException is raised, tries to
        login and do it again.
        """
        try:
            return self.raw_request(*args, **kwargs)
        except TDAuthorizationException:
            self.login()
            return self.raw_request(*args, **kwargs)

    def json_request(self, *args, **kwargs):
        """
        Simple wrapper around request() that converts JSON response into
        a Python object.
        """
        resp = self.request(*args, **kwargs)
        return json.loads(resp.text)

    def login(self):
        """
        This posts the login data.
        """
        resp = self.request(method='post',
                            url_stem='auth/loginadmin',
                            data={'BEID': self.BEID,
                                  'WebServicesKey': self.WebServicesKey,
                              },
                            bearer_required=False
                        )
        self.bearer_token = resp.text

    def json_request_roller(self, *args, **kwargs):
        """
        Will always return a list. If TD returns one element, you'll get a
        list.
        """
        objs = self.json_request(*args, **kwargs)
        if isinstance(objs, dict):
            # TD returned one element
            return [objs]
        else:
            return objs

    def new_ci(self, type_id, name):
        # FIXME this needs to be redone probably as
        # TDConfigurationItem({new_struct}).save()
        td_struct=self.json_request(method='post',
                                    url_stem='cmdb',
                                    data={'TypeID': type_id,
                                        'Name': name,
                                      })
        return api.cmdb.TDConfigurationItem(td_struct=td_struct)
