#!python
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
import tdapi
from tdapi.ticket import TDTicketAppFactory

# Your instance-specific variables:
BEID='beid-goes-here'
WebServicesKey='wsk-goes-here'
TICKET_APP_ID='123'
STATUS_1=12345
STATUS_2=23456
CLOSED=34567

# code begins:

TDTicket = TDTicketAppFactory(app_id=TICKET_APP_ID)

if __name__ == '__main__':
    td_conn = tdapi.TDConnection(
        BEID=BEID,
        WebServicesKey=WebServicesKey,
        )
    tdapi.TD_CONNECTION = td_conn

    # tickets in Status #2 need to be closed
    for ticket in TDTicket.objects.search({
            'StatusIDs': [STATUS_2],
            }):
        ticket.add_to_feed_and_notify_all(status_id=CLOSED,
                                          is_private=False,
                                          comments='Ticket closed')
                                          

    # tickets in Status #1 need to go to Status #2
    for ticket in TDTicket.objects.search({
            'StatusIDs': [STATUS_1],
            }):
        ticket.add_to_feed_and_notify_all(status_id=STATUS_2,
                                          is_private=False,
                                          comments='Ticket progressing to Status 2')
