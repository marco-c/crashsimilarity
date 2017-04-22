import os
import unittest

from crashsimilarity.cache import TracesCache, DownloaderCache


class TestTracesCache(unittest.TestCase):
    def test_traces_cache_build(self):
        lines = ['{"proto_signature": "a | CAPITAL_LETTERS | c", "uuid": "1", "signature": "c"}',
                 '{"proto_signature": "a | b | d", "uuid": "2", "signature": "d"}',
                 '{"proto_signature": "a | x | d", "uuid": "3", "signature": "d"}',
                 '{"proto_signature": "a | b | e", "uuid": "4", "signature": "same"}',
                 '{"proto_signature": "with | @0x end | drop", "uuid": "5", "signature": "drop"}',
                 '{"proto_signature": "with | xul.dll@", "uuid": "6", "signature": "ignored"}',
                 '{"proto_signature": "a | b | e", "uuid": "7", "signature": "same"}']
        cache = TracesCache.build(lines)
        expected = [(['a', 'capital_letters', 'c'], 'c', '1'),
                    (['a', 'b', 'd'], 'd', '2'),
                    (['a', 'x', 'd'], 'd', '3'),
                    (['a', 'b', 'e'], 'same', '4'),
                    (['with', '@0x', 'drop'], 'drop', '5')]
        self.assertEqual(cache.traces, expected)


class TestDownloaderCache(unittest.TestCase):
    default_cache_file_name = 'downloader_cache.pickle'
    other_file_name = 'other.pickle'

    # don't want to use pyfake or mock os.system calls for such a small task
    def setUp(self):
        if os.path.exists(self.default_cache_file_name):
            os.remove(self.default_cache_file_name)
        if os.path.exists(self.other_file_name):
            os.remove(self.other_file_name)

    def test_build(self):
        cache = DownloaderCache.build()
        self.assertDictEqual(dict(), cache)
        cache = DownloaderCache()
        self.assertDictEqual(dict(), cache)
        cache = DownloaderCache({'foo': 1, 42: 'bar'})
        self.assertDictEqual({'foo': 1, 42: 'bar'}, cache)
        cache = DownloaderCache.build({'foo': 1, 42: 'bar'})
        self.assertDictEqual({'foo': 1, 42: 'bar'}, cache)
