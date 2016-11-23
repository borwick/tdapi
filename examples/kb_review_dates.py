#!python
from datetime import date
import logging
logging.basicConfig(level=logging.INFO)

import tdapi
from tdapi.kb import TDKnowledgeArticle

user = 'web-user-goes-here'
password = 'web-password-goes-here'

def today_str():
    return date.today().isoformat()


if __name__ == '__main__':
    td_conn = tdapi.TDUserConnection(username=user,
                                     password=password)
    tdapi.set_connection(td_conn)
    default_review_date = today_str()
    
    for article in TDKnowledgeArticle.objects.all():
        review_date = article.get('ReviewDateUtc')
        if review_date is None:
            logging.info("Setting review date for %s", article)
            try:
                article.update({'ReviewDateUtc': default_review_date})
            except tdapi.TDException:
                logging.warning("Could not update %s", article.get('ID'))
