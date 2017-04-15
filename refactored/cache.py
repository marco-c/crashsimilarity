import json
import logging
import pickle

import utils


class Cache(object):
    def __init__(self, traces=None, downloader_cache=None):
        # TODO: construct from Dict[signature, List[(stack_trace, uuid)] ?
        self.downloader_cache = downloader_cache if downloader_cache else dict()
        self.traces = traces if traces else []

    @staticmethod
    def build(stream):
        """build from downloaded archives"""

        # Exclude stack traces without symbols.
        def should_skip(stack_trace):
            return any(call in stack_trace for call in ['xul.dll@', 'XUL@', 'libxul.so@'])

        logging.debug('building cache from stream...')

        traces = []
        already_selected = set()
        for line in stream:
            data = json.loads(line)
            if should_skip(data['proto_signature']):
                continue
            processed = utils.preprocess(data['proto_signature'])
            if frozenset(processed) not in already_selected:
                # TODO: named tuple?
                traces.append((processed, data['signature'].lower(), data['uuid']))
                already_selected.add(frozenset(processed))
        return Cache(traces=traces)

    @staticmethod
    def try_load_or_build(stream):
        traces, downloads = Cache._load()
        if not traces:
            cache = Cache.build(stream)
            cache._dump_traces_on_disk()
            cache.downloader_cache = downloads
            return cache
        return Cache(traces, downloads)

    def _dump_traces_on_disk(self, file_name='traces_cache.pickle'):
        pickle.dump(self.traces, open(file_name, 'wb'))
        logging.debug('traces dumped on disk')

    @staticmethod
    def _load():
        try:
            traces = pickle.load(open('traces_cache.pickle', 'rb'))
            logging.debug('traces cache read from disk')
        except:
            traces = list()
        try:
            downloads = pickle.load(open('downloads_cache.pickle', 'rb'))
            logging.debug('downloads cache read from disk')
        except:
            downloads = dict()
        return traces, downloads

    def update_downloader_cache(self, key, value):
        self.downloader_cache[key] = value
        pickle.dump(self.downloader_cache, open('downloads_cache.pickle', 'wb'))
