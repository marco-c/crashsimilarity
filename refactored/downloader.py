from datetime import timedelta
import logging

import utils


class Downloader(object):
    SUPER_SEARCH_URL = 'https://crash-stats.mozilla.com/api/SuperSearch'

    def __init__(self, cache=None):
        self.cache = cache

    def download_stack_traces_for_signature(self, signature, period=timedelta(days=31), traces_num=100):
        from_date = utils.utc_today() - period

        key = ('traces', signature, from_date)
        if self.cache and key in self.cache.downloader_cache:
            logging.debug('get data from cache')
            return self.cache.downloader_cache[key]

        params = {
            'signature': '=' + signature,
            'date': ['>=' + str(from_date)],
            '_facets': ['proto_signature'],
            '_facets_size': traces_num,
            '_results_number': 0
        }
        res = utils.get_with_retries(self.SUPER_SEARCH_URL, params)
        records = res.json()['facets']['proto_signature']

        traces = list(set([r['term'] for r in records]))
        if self.cache:
            self.cache.update_downloader_cache(key, traces)
        return traces
