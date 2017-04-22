from datetime import timedelta
import logging

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry

from crashsimilarity import utils


class Downloader(object):
    def __init__(self, cache=None):
        self._cache = cache

    @staticmethod
    def _json_or_raise(response):
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_with_retries(url, params=None, headers=None):
        # can't be tested with requests_mock.Mocker() for unknown reason
        s = requests.Session()
        s.mount(url, HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1, status_forcelist=[429])))
        return s.get(url, params=params, headers=headers)


class BugzillaDownloader(Downloader):
    _URL = 'https://bugzilla.mozilla.org/rest/bug'

    def __init__(self, cache=None):
        super().__init__(cache)

    def download_signatures(self, bug_id):
        key = ('bugzilla_bug', bug_id, utils.utc_today())
        if self._cache and key in self._cache:
            logging.debug('get data from cache')
            return self._cache[key]

        params = {'id': bug_id}
        response = self.get_with_retries(self._URL, params)
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


class SocorroDownloader(Downloader):
    _SUPER_SEARCH_URL = 'https://crash-stats.mozilla.com/api/SuperSearch'
    _PROCESSED_CRASH_URL = 'https://crash-stats.mozilla.com/api/ProcessedCrash'

    def __init__(self, cache=None):
        super().__init__(cache)

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
        response = self.get_with_retries(self._SUPER_SEARCH_URL, params)
        records = self._json_or_raise(response)['facets']['proto_signature']
        traces = set([r['term'] for r in records])

        if self._cache:
            self._cache[key] = traces
        return traces

    def download_crash(self, uuid):
        key = ('crash_for_uuid', uuid, utils.utc_today())
        if self._cache and key in self._cache:
            logging.debug('get data from cache')
            return self._cache[key]

        params = {'crash_id': uuid}
        crash = self._json_or_raise(self.get_with_retries(self._PROCESSED_CRASH_URL, params))

        if self._cache:
            self._cache[key] = crash
        return crash
