from datetime import timedelta
import logging

from crashsimilarity import utils


class Downloader(object):
    _SUPER_SEARCH_URL = 'https://crash-stats.mozilla.com/api/SuperSearch'
    _PROCESSED_CRASH_URL = 'https://crash-stats.mozilla.com/api/ProcessedCrash'
    _BUGZILLA_BUG_URL = 'https://bugzilla.mozilla.org/rest/bug'

    def __init__(self, cache=None):
        self._cache = cache

    def download_stack_traces_for_signature(self, signature, traces_num=100, period=timedelta(days=31)):
        from_date = utils.utc_today() - period

        key = ('traces_for_signature', signature, utils.utc_today(), from_date)
        if self._cache and key in self._cache:
            logging.debug('get data from cache')
            return self._cache[key]

        params = {
            'signature': '=' + signature,
            'date': ['>=' + str(from_date)],
            '_facets': ['proto_signature'],
            '_facets_size': traces_num,
            '_results_number': 0
        }
        response = utils.get_with_retries(self._SUPER_SEARCH_URL, params)
        records = self._json_or_raise(response)['facets']['proto_signature']
        traces = set([r['term'] for r in records])

        if self._cache:
            self._cache[key] = traces
        return traces

    def download_crash_for_id(self, uuid):
        key = ('crash_for_uuid', uuid, utils.utc_today())
        if self._cache and key in self._cache:
            logging.debug('get data from cache')
            return self._cache[key]

        params = {'crash_id': uuid}
        crash = self._json_or_raise(utils.get_with_retries(self._PROCESSED_CRASH_URL, params))

        if self._cache:
            self._cache[key] = crash
        return crash

    def download_signatures_for_bug_id(self, bug_id):
        key = ('bugzilla_bug', bug_id, utils.utc_today())
        if self._cache and key in self._cache:
            logging.debug('get data from cache')
            return self._cache[key]

        params = {'id': bug_id}
        response = utils.get_with_retries(self._BUGZILLA_BUG_URL, params)
        signatures = set()
        for sig in self._json_or_raise(response)['bugs'][0]['cf_crash_signature'].split('\r\n'):
            pos = sig.find('[@')
            if pos != -1:
                sig = sig[pos + 2:]
            pos = sig.rfind(']')
            if pos != -1:
                sig = sig[:pos]
            signatures.add(sig.strip())

        if self._cache:
            self._cache[key] = list(signatures)
        return list(signatures)

    @staticmethod
    def _json_or_raise(response):
        response.raise_for_status()
        return response.json()
