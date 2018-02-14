import pickle
from abc import abstractmethod

from crashsimilarity.stacktrace_utils import StackTraceProcessor


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
        except FileNotFoundError:
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
        except AttributeError:
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
    def build(traces, file_name=None):
        return TracesCache(traces, file_name)

    @staticmethod
    def build_from_raw_traces(traces, file_name=None):
        return TracesCache.build(list(StackTraceProcessor.process(traces)), file_name)
