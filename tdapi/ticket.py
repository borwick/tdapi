import copy
import random
import string

import tdapi
import tdapi.obj


class TDBaseTicketManager(tdapi.obj.TDObjectManager):
    """
    Each ticketing application manager inherits from this base ticket
    manager. The `APP_ID` variable is stored in the ticket
    manager--that's the magic that makes each class different. This
    also keeps you from having to pass the application ID across calls.
    """
    APP_ID = None

    def _copy_or_create(self, data, data_to_merge=None):
        if data is None:
            new_data = {}
        else:
            new_data = copy.deepcopy(data)
        new_data.update(data_to_merge)
        return new_data

    @classmethod
    def url_prefix(cls):
        return '{}/tickets'.format(cls.APP_ID)

    @classmethod
    def make_url(cls, url_stem):
        return cls.url_prefix() + url_stem

    def search(self, data):
        return [self.object_class(td_struct)
                for td_struct
                in tdapi.TD_CONNECTION.json_request_roller(
                    method='post',
                    url_stem=self.make_url('/search'),
                    data=data,
                )]

    def get(self, ticket_id):
        url_stem = self.make_url('/{}'.format(ticket_id))
        td_struct = tdapi.TD_CONNECTION.json_request_roller(
            method='get',
            url_stem=url_stem)
        assert len(td_struct) == 1
        return self.object_class(td_struct[0])


class TDBaseTicket(tdapi.obj.TDObject):
    """
    Ticket classes for each ticket application inherit from this base
    ticket class. It uses the APP_ID to build URLs
    """
    APP_ID = None

    def __init__(self, *args, **kwargs):
        super(TDBaseTicket, self).__init__(*args, **kwargs)
        self._single_queried = False

    def ticket_id(self):
        return self.get('ID')
    
    def url(self):
        return '{}/tickets/{}'.format(self.APP_ID, self.ticket_id())

    def __str__(self):
        return self.get('Title')

    def ticket_id(self):
        return self.get('ID')

    def _ensure_single_query(self):
        if self._single_queried is False:
            self.td_struct = tdapi.TD_CONNECTION.json_request(
                method='get',
                url_stem=self.url()
                )
            self._single_queried = True


    def add_to_feed(self, status_id, is_private, comments, notify):
        feed_update_url = self.url() + '/feed'
        data = {'NewStatusID': status_id,
                'IsPrivate': is_private,
                'Comments': comments,
                'Notify': notify}
                
        updated_item = tdapi.TD_CONNECTION.json_request(method='post',
                                                        url_stem=feed_update_url,
                                                        data=data)
        return updated_item

    def notify_values(self):
        return [x['Value']
                for x
                in self.single_query_get('Notify')]

    def add_to_feed_and_notify_all(self, status_id, is_private, comments):
        self.add_to_feed(status_id=status_id,
                         is_private=is_private,
                         comments=comments,
                         notify=self.notify_values())

def TDTicketAppFactory(app_id):
    class TDTicketManager(TDBaseTicketManager):
        APP_ID = app_id

    class TDTicket(TDBaseTicket):
        APP_ID = app_id
    tdapi.obj.relate_cls_to_manager(TDTicket, TDTicketManager)
    return TDTicket
