import unittest
from datetime import timedelta

import requests
import requests_mock

from crashsimilarity import utils
from crashsimilarity.downloader import Downloader


class DownloaderTest(unittest.TestCase):
    def test_download_signatures_for_bug_id(self):
        crash_signatures = ['@0x0 | idmcchandler7_64.dll@0x1feaf',
                            '@0x0 | idmcchandler7_64.dll@0x238bf',
                            '@0x0 | idmcchandler7_64.dll@0x233af',
                            '@0x0 | idmcchandler7_64.dll@0x233cf',
                            '@0x0 | idmcchandler7_64.dll@0x22e6f',
                            '@0x0 | idmcchandler7_64.dll@0x22e7f',
                            '@0x0 | idmcchandler7_64.dll@0x2343f',
                            '@0x0 | idmcchandler5_64.dll@0x1f0ea',
                            '@0x0 | ffi_call']
        crash_signatures2 = [u'std::list<T>::clear', u'std::list<T>::clear | CDeviceChild<T>::~CDeviceChild<T>']
        resp = Downloader().download_signatures_for_bug_id('1333486')
        resp2 = Downloader().download_signatures_for_bug_id('1308863')
        self.assertCountEqual(resp, crash_signatures)
        self.assertCountEqual(resp2, crash_signatures2)

    # cache tests can fail if started just before midnight. nobody should care
    def test_downloader_actual_cache(self):
        days_42 = timedelta(days=42)
        cache = {
            'unrelated_key': 'unrelated_key',
            ('crash_for_uuid', '42', utils.utc_today()): 'crash for 42',
            ('traces_for_signature', 'js::whatever', utils.utc_today(),
             utils.utc_today() - days_42): 'traces for js::whatever',
            ('bugzilla_bug', '12345', utils.utc_today()): 'bug with id 12345'
        }
        downloader = Downloader(cache)
        self.assertEqual(downloader.download_crash_for_id('42'), 'crash for 42')
        self.assertEqual(downloader.download_stack_traces_for_signature('js::whatever', period=days_42),
                         'traces for js::whatever')
        self.assertEqual(downloader.download_signatures_for_bug_id('12345'), 'bug with id 12345')

    def test_downloader_outdated_cache(self):
        days_1 = timedelta(days=1)
        days_42 = timedelta(days=42)
        cache = {
            'unrelated_key': 'unrelated_key',
            ('crash_for_uuid', '42', utils.utc_today() - days_1): 'crash for 42',
            ('traces_for_signature', 'js::whatever', utils.utc_today(),
             utils.utc_today() - days_42): 'traces for js::whatever',
            ('bugzilla_bug', '12345', utils.utc_today()): 'bug with id 12345'
        }
        downloader = Downloader(cache)
        with requests_mock.Mocker() as m:
            expected_signature = {'proto_signature': 'new signature'}
            m.get(downloader._PROCESSED_CRASH_URL, json=expected_signature)
            actual = downloader.download_crash_for_id('42')
            self.assertEqual(actual, expected_signature)

            response_json = {'bugs': [{'whatever': 'unused',
                                       'cf_crash_signature': "[@ @0x0 | sig1]\r\n[@ @0x0 | sig1]\r\n[@ @0x0 | sig2]"}]}
            expected_signatures = ['@0x0 | sig1', '@0x0 | sig2']
            m.get(downloader._BUGZILLA_BUG_URL, json=response_json)
            actual = downloader.download_signatures_for_bug_id('239')
            self.assertCountEqual(actual, expected_signatures)

        updated_cache = cache
        updated_cache[('crash_for_uuid', '42', utils.utc_today())] = expected_signature
        updated_cache[('bugzilla_bug', '239', utils.utc_today())] = 'bug with id 239'
        self.assertDictEqual(cache, updated_cache)

    def test_downloader_404(self):
        downloader = Downloader()
        with self.assertRaises(Exception) as ctx:
            with requests_mock.Mocker() as m:
                m.get(downloader._PROCESSED_CRASH_URL, [{'status_code': 404}])
                downloader.download_crash_for_id('42')
            self.assertIsInstance(ctx.exception, requests.exceptions.HTTPError)
            self.assertIn(404, ctx.exception)
