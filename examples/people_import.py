#!python
"""
Example code to send a file to the people import API.

Use as:

        python people_import.py \
             --BEID BEID-GOES-HERE \
             --WebServicesKey WEBSERVICESKEY-GOES-HERE \
             --sandbox \ # if you want to update the sandbox
             --xlsx import-file.xlsx
"""
import argparse
import sys
import logging

import tdapi

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="People importer")
    parser.add_argument('--BEID', required=True)
    parser.add_argument('--WebServicesKey', required=True)
    parser.add_argument('--xlsx', required=True)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--sandbox',
                        help='Use the sandbox environment',
                        action='store_true')
    args = parser.parse_args()

    xlsx_fh = open(args.xlsx, 'rb')

    td_conn = tdapi.TDConnection(BEID=args.BEID,
                                 WebServicesKey=args.WebServicesKey,
                                 preview=args.preview,
                                 sandbox=args.sandbox)
    tdapi.TD_CONNECTION = td_conn

    files = {'import.xlsx': ('import.xlsx',
                             xlsx_fh,
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )}
    td_conn.files_request(method='post',
                          url_stem='people/import',
                          files=files)

