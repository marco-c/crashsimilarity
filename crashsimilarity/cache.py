import json
import pickle
from abc import abstractmethod

import logging

from crashsimilarity import utils


class BaseCache(object):
    def __init__(self, name, file_name=None):
        self.name = name
        self.file_name = file_name if file_name else '{}_cache.pickle'.format(self.name)

    @staticmethod
    @abstractmethod
    def build(data, file_name=None):
        pass

    def dump(self, file_name=None):
        if not file_name:
            file_name = self.file_name
        pickle.dump(self, open(file_name, 'wb'))

    @staticmethod
    def load(file_name):
        try:
            return pickle.load(open(file_name, 'rb'))
        except:
            return None

    def try_load_or_build(self, file_name=None, data=None):
        if not file_name:
            file_name = self.file_name
        rv = self.load(file_name)
        return rv if rv else self.build(data)


class DownloaderCache(dict, BaseCache):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)
        BaseCache.__init__(self, "downloader")

    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        try:
            self.dump()
        except:
            pass

    @staticmethod
    def build(data=None, file_name=None):
        d = DownloaderCache(data) if data else DownloaderCache()
        if file_name:
            d.file_name = file_name
        d.dump()
        return d


class TracesCache(BaseCache):
    def __init__(self, traces=None, file_name=None):
        BaseCache.__init__(self, "traces", file_name)
        self.traces = traces if traces else []

    @staticmethod
    def build(stream, file_name=None):
        """build from downloaded archives"""

        # Exclude stack traces without symbols.
        def should_skip(stack_trace):
            return any(call in stack_trace for call in ['xul.dll@', 'XUL@', 'libxul.so@'])

        logging.info('building cache from stream...')

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
        cache = TracesCache(traces)
        if file_name:
            cache.file_name = file_name
        return cache
