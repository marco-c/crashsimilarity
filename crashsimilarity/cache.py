import pickle
from abc import abstractmethod


class BaseCache(object):
    def __init__(self, name, file_name=None):
        self.name = name
        self.file_name = file_name if file_name else '{}_cache.pickle'.format(self.name)

    @abstractmethod
    def build(self, data):
        pass

    def dump(self, file_name=None):
        if not file_name:
            file_name = self.file_name
        pickle.dump(self, open(file_name, 'wb'))

    def _load(self, file_name=None):
        try:
            if not file_name:
                file_name = self.file_name
            return pickle.load(open(file_name, 'rb'))
        except:
            return None

    def try_load_or_build(self, data=None, file_name=None):
        rv = self._load(file_name)
        return rv if rv else self.build(data)


class DownloaderCache(dict, BaseCache):
    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)
        BaseCache.__init__(self, "downloader")

    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        try:
            self.dump()
        except:
            pass

    def build(self, data):
        return DownloaderCache(**data)
