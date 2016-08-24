#!python
import tdapi
from tdapi.ticket import TDTicketAppFactory

BEID='beid-goes-here'
WebServicesKey='wsk-goes-here'
TICKET_APP_ID='346'

STATUS_1=16569
STATUS_2=16570
CLOSED=11120

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
