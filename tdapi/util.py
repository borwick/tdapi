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


class KeyMatcher(object):
    """
    Lets you define keys that should be tracked. You then add()
    matches. You can then match() against the keys you defined.

    The reason this exists is to support a "hierarchy" of matches. For
    example, you may want to match on key A--and if there's a match,
    you're done. Then if there's no match on key A, try key B. &c.
    """
    def __init__(self, keys_to_track):
        """
        keys_to_track -- order is important! Matches will be tested in
        this order.
        """
        self.keys_to_track = keys_to_track
        self.tracker = {}
        for key_to_track in self.keys_to_track:
            self.tracker[key_to_track] = {}

    def add(self, obj, match_dict):
        """
        Add obj as a match for match_dict values.

        Checks to make sure match_dict keys are valid.

        Note: match_dict values will be ignored if they do not exist,
        are None, or are ''.
        """
        for match_key in match_dict.keys():
            assert match_key in self.keys_to_track

        for key_to_track in self.keys_to_track:
            if match_dict.has_key(key_to_track):
                match_val = match_dict[key_to_track]
                if match_val is None or match_val == '':
                    pass
                else:
                    self.tracker[key_to_track][match_val] = obj

    def match(self, match_dict):
        """
        Find a match using match_dict. Returns None if there is no match.

        Checks to make sure match_dict keys are valid.
        """
        for match_key in match_dict.keys():
            assert match_key in self.keys_to_track

        for key_to_track in self.keys_to_track:
            if match_dict.has_key(key_to_track):
                match_val = match_dict[key_to_track]
                if self.tracker[key_to_track].has_key(match_val):
                    return self.tracker[key_to_track][match_val]
        return None

    def keys(self):
        return self.keys_to_track


class KeyMatchingCachedRecordManager(CachedRecordManager):
    """
    Define `KEYS_TO_TRACK` property and an _add_matches() method.
    """
    def __init__(self, *args, **kwargs):
        super(KeyMatchingCachedRecordManager, self).__init__(*args, **kwargs)
        self.key_matcher = KeyMatcher(self.KEYS_TO_TRACK)
        self._add_matches()

    def _add_matches(self):
        """
        Utility function to populate key_matcher from self.records.
        """
        for record in self.records:
            match_dict={key_to_track: record.get(key_to_track)
                         for key_to_track in self.key_matcher.keys()}
            self.key_matcher.add(obj=record,
                                 match_dict=match_dict)

    def match(self, **match_dict):
        return self.key_matcher.match(match_dict)
