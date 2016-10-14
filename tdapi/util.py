class CachedRecordManager(object):
    """
    This is a horrible class to let you do client-side comparisons
    rather than relying on the API's search. Only use this if the API
    does not provide a mechanism to search the way you want.

    Example:
      cached_records = CachedRecordsManager(TDPerson.objects.all())
      users = cached_records.find({'AuthenticationUserName': 'x'})
    """
    def __init__(self, records):
        self.records = records

    def find(self, match_dict, match_all=True):
        found_records = []
        for record in self.records:
            if self._matches(record, match_dict, match_all):
                found_records.append(record)
        return found_records

    def _matches(self, record, match_dict, match_all):
        assert len(match_dict) > 0
        for (match_key, match_val) in match_dict.items():
            if record.get(match_key) == match_val:
                if match_all is False:
                    return True
                else:
                    # need to match all so keep checking
                    continue
            else:
                return False
        return True

