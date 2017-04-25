import os
import unittest

from crashsimilarity.cache import TracesCache, DownloaderCache
from tests.test_utils import StackTraceProcessorTest


class CacheTest(unittest.TestCase):
    default_cache_file_name = 'default.pickle'
    other_file_name = 'other.pickle'

    # don't want to use pyfake or mock os.system calls for such a small task
    def setUp(self):
        if os.path.exists(self.default_cache_file_name):
            os.remove(self.default_cache_file_name)
        if os.path.exists(self.other_file_name):
            os.remove(self.other_file_name)

    def tearDown(self):
        self.setUp()


class TestTracesCache(CacheTest):
    default_cache_file_name = 'traces_cache.pickle'

    def test_traces_cache_build_from_raw_traces(self):
        """we need to be sure that `build_from_raw_traces` is just a proxy call for StackTraceProcessor.process(...)"""
        cache = TracesCache.build_from_raw_traces(StackTraceProcessorTest.raw_traces)
        self.assertEqual(cache.traces, StackTraceProcessorTest.expected_traces)
        self.assertEqual(cache.name, 'traces')
        self.assertEqual(cache.file_name, 'traces_cache.pickle')

    def test_save_load(self):
        cache = TracesCache.build([(['a', 'b', 'd'], 'd', '2')])
        cache.dump(self.default_cache_file_name)
        from_disk = TracesCache.load(self.default_cache_file_name)
        self.assertEqual(from_disk.traces, cache.traces)
        from_disk = TracesCache.load(self.other_file_name)
        self.assertIsNone(from_disk)


class TestDownloaderCache(CacheTest):
    default_cache_file_name = 'downloader_cache.pickle'

    def test_build(self):
        cache = DownloaderCache.build()
        self.assertDictEqual(cache, dict())
        self.assertEqual(cache.name, 'downloader')
        self.assertEqual(cache.file_name, self.default_cache_file_name)
        cache = DownloaderCache()
        self.assertDictEqual(cache, dict())
        cache = DownloaderCache({'foo': 1, 42: 'bar'})
        self.assertDictEqual(cache, {'foo': 1, 42: 'bar'})
        cache = DownloaderCache.build({'foo': 1, 42: 'bar'}, file_name=self.other_file_name)
        self.assertDictEqual(cache, {'foo': 1, 42: 'bar'})
        self.assertEqual(cache.file_name, self.other_file_name)

    def test_save_on_update(self):
        cache = DownloaderCache()
        cache['foo'] = 1
        from_disk = DownloaderCache.load(cache.file_name)
        self.assertEqual(from_disk, cache)
        cache['bar'] = 2
        self.assertNotEqual(from_disk, cache)
        from_disk = DownloaderCache.load(cache.file_name)
        self.assertEqual(from_disk, cache)

    def test_try_load_or_build(self):
        cache = DownloaderCache().try_load_or_build(self.default_cache_file_name, {'foo': 1, 42: 'bar'})
        self.assertDictEqual(cache, {'foo': 1, 42: 'bar'})
        from_disk = DownloaderCache.load(cache.file_name)
        self.assertEqual(from_disk, cache)
