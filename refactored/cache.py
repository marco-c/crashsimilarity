import json
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

        # TODO: is it possible to have different `signature`s for one `proto_signature` ?
        # Exclude stack traces without symbols.
        def should_skip(stack_trace):
            return any(call in stack_trace for call in ['xul.dll@', 'XUL@', 'libxul.so@'])

        traces = []
        already_selected = set()
        for line in stream:
            data = json.loads(line)
            if should_skip(data['proto_signature']):
                continue
            processed = utils.preprocess(data['proto_signature'])
            if frozenset(processed) not in already_selected:
                # TODO: named tuple?
                traces.append((processed, data['signature'], data['uuid']))
                already_selected.add(frozenset(processed))
        return Cache(traces=traces)

    @staticmethod
    def try_load_or_build(stream):
        try:
            return Cache.load()
        except:
            return Cache.build(stream)

    def dump_traces_on_disk(self, file_name='traces_cache.pickle'):
        pickle.dump(self.traces, open(file_name, 'wb'))

    @staticmethod
    def load():
        traces = pickle.load(open('traces_cache.pickle', 'rb'))
        try:
            downloads = pickle.load(open('downloads_cache.pickle', 'rb'))
        except:
            downloads = dict()
        return Cache(traces, downloads)

    def update_downloader_cache(self, key, value):
        self.downloader_cache[key] = value
        pickle.dump(self.downloader_cache, open('downloads_cache.pickle', 'wb'))
