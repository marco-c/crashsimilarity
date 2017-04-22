from datetime import timedelta
import logging

from crashsimilarity import utils


class Downloader(object):
    SUPER_SEARCH_URL = 'https://crash-stats.mozilla.com/api/SuperSearch'
    PROCESSED_CRASH_URL = 'https://crash-stats.mozilla.com/api/ProcessedCrash'
    BUGZILLA_BUG_URL = 'https://bugzilla.mozilla.org/rest/bug'

    def __init__(self, cache=None):
        self.cache = cache

    def download_stack_traces_for_signature(self, signature, traces_num=100, period=timedelta(days=31)):
        from_date = utils.utc_today() - period

        key = ('traces_for_signature', signature, utils.utc_today(), from_date)
        if self.cache and key in self.cache:
            logging.debug('get data from cache')
            return self.cache[key]

        params = {
            'signature': '=' + signature,
            'date': ['>=' + str(from_date)],
            '_facets': ['proto_signature'],
            '_facets_size': traces_num,
            '_results_number': 0
        }
        res = utils.get_with_retries(self.SUPER_SEARCH_URL, params)
        records = res.json()['facets']['proto_signature']
        traces = set([r['term'] for r in records])

        if self.cache:
            self.cache[key] = traces
        return traces

    def download_crash_for_id(self, uuid):
        key = ('crash_for_uuid', uuid, utils.utc_today())
        if self.cache and key in self.cache:
            logging.debug('get data from cache')
            return self.cache[key]

        params = {'crash_id': uuid}
        crash = utils.get_with_retries(self.PROCESSED_CRASH_URL, params).json()

        if self.cache:
            self.cache[key] = crash
        return crash

    def download_signatures_for_bug_id(self, bug_id):
        key = ('bugzilla_bug', bug_id, utils.utc_today())
        if self.cache and key in self.cache:
            logging.debug('get data from cache')
            return self.cache[key]

        params = {'id': bug_id}
        response = utils.get_with_retries(self.BUGZILLA_BUG_URL, params)
        signatures = set()
        for sig in response.json()['bugs'][0]['cf_crash_signature'].split('\r\n'):
            pos = sig.find('[@')
            if pos != -1:
                sig = sig[pos + 2:]
            pos = sig.rfind(']')
            if pos != -1:
                sig = sig[:pos]
            signatures.add(sig.strip())

        if self.cache:
            self.cache[key] = list(signatures)
        return list(signatures)
