import unittest
from datetime import timedelta

import requests
import requests_mock
from itertools import islice

from crashsimilarity import utils
from crashsimilarity.downloader import BugzillaDownloader, SocorroDownloader, Downloader


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
        resp = BugzillaDownloader().download_signatures('1333486')
        resp2 = BugzillaDownloader().download_signatures('1308863')
        self.assertCountEqual(resp, crash_signatures)
        self.assertCountEqual(resp2, crash_signatures2)

    def test_download_bugs(self):
        bugzilla = BugzillaDownloader()
        bugs_list = bugzilla.download_bugs('2018-01-01', '2018-02-01')
        self.assertIsInstance(bugs_list, list)
        self.assertGreater(len(bugs_list), 0)
        for bug in bugs_list:
            self.assertIn('id', bug)
            self.assertIn('cf_crash_signature', bug)
            self.assertIsInstance(bug['id'], int)
            self.assertIsInstance(bug['cf_crash_signature'], list)

    # cache tests can fail if started just before midnight. nobody should care
    def test_downloader_actual_cache(self):
        days_42 = timedelta(days=42)
        cache = {
            'unrelated_key': 'unrelated_key',
            ('crash_for_uuid', '42', utils.utc_today()): 'crash for 42',
            ('traces_for_signature', 'js::whatever', utils.utc_today()): 'traces for js::whatever',
            ('bugzilla_bug', '12345', utils.utc_today()): 'bug with id 12345'
        }
        socorro = SocorroDownloader(cache)
        bugzilla = BugzillaDownloader(cache)
        self.assertEqual(socorro.download_stack_traces_for_signature('js::whatever', period=days_42),
                         'traces for js::whatever')
        self.assertEqual(bugzilla.download_signatures('12345'), 'bug with id 12345')

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
        socorro = SocorroDownloader(cache)
        bugzilla = BugzillaDownloader(cache)
        with requests_mock.Mocker() as m:
            expected_signature = {'proto_signature': 'new signature'}
            m.get(socorro._PROCESSED_CRASH_URL, json=expected_signature)
            actual = socorro.download_crash('42')
            self.assertEqual(actual, expected_signature)

            response_json = {'bugs': [{'whatever': 'unused',
                                       'cf_crash_signature': "[@ @0x0 | sig1]\r\n[@ @0x0 | sig1]\r\n[@ @0x0 | sig2]"}]}
            expected_signatures = ['@0x0 | sig1', '@0x0 | sig2']
            m.get(bugzilla._URL, json=response_json)
            actual = bugzilla.download_signatures('239')
            self.assertCountEqual(actual, expected_signatures)

        updated_cache = cache
        updated_cache[('crash_for_uuid', '42', utils.utc_today())] = expected_signature
        updated_cache[('bugzilla_bug', '239', utils.utc_today())] = 'bug with id 239'
        self.assertDictEqual(cache, updated_cache)

    def test_download_day_crashes(self):
        socorro = SocorroDownloader()
        expected = [{'proto_signature': 'fun1 | fun2 | fun3', 'signature': 'sig1', 'uuid': 'uuid-1'},
                    {'proto_signature': 'fun6 | fun7 | fun8', 'signature': 'sig2', 'uuid': 'uuid-2'},
                    {'proto_signature': 'fun10 | fun11 | fun12', 'signature': 'sig3', 'uuid': 'uuid-3'},
                    {'proto_signature': 'gcd_ | dfs | LCA', 'signature': 'sig4', 'uuid': 'uuid-4'},
                    {'proto_signature': '<T>cpp | js::foo | js::bar_x', 'signature': 'sig5', 'uuid': 'uuid-5'}
                    ]
        first_part = {'errors': 'whatever', 'facets': {}, 'hits': expected[:2], 'total': 5}
        second_part = {'errors': 'whatever', 'facets': {}, 'hits': expected[2:4], 'total': 5}
        third_part = {'errors': 'whatever', 'facets': {}, 'hits': expected[4:], 'total': 5}
        with requests_mock.Mocker() as m:
            m.get(socorro._SUPER_SEARCH_URL, [{'json': first_part}, {'json': second_part}, {'json': third_part}])
            res2 = socorro.download_day_crashes(utils.utc_today(), crashes_per_request=2)
            self.assertCountEqual(list(res2), expected)

        with requests_mock.Mocker() as m:
            m.get(socorro._SUPER_SEARCH_URL, json={'hits': expected, 'total': 5})
            res10 = socorro.download_day_crashes(utils.utc_today(), crashes_per_request=10)
            self.assertCountEqual(list(res10), expected)

        # can get data before exception
        with self.assertRaises(Exception) as ctx:
            with requests_mock.Mocker() as m:
                m.get(socorro._SUPER_SEARCH_URL, [{'json': first_part}, {'status_code': 404}])
                res = socorro.download_day_crashes(utils.utc_today(), crashes_per_request=2)
                first2 = list(islice(res, 2))
                other = list(res)
                self.assertCountEqual(first2, expected[:2])
                self.assertIs(other, [])
                self.assertIsInstance(ctx.exception, requests.exceptions.HTTPError)
                self.assertIn(404, ctx.exception)

    def test_downloader_404(self):
        downloader = SocorroDownloader()
        with self.assertRaises(Exception) as ctx:
            with requests_mock.Mocker() as m:
                m.get(downloader._PROCESSED_CRASH_URL, [{'status_code': 404}])
                downloader.download_crash('42')
            self.assertIsInstance(ctx.exception, requests.exceptions.HTTPError)
            self.assertIn(404, ctx.exception)

    def test_get_with_retries_200(self):
        bug_id = '1308863'
        resp = Downloader.get_with_retries(BugzillaDownloader._URL, params={'id': bug_id})
        self.assertEqual(resp.status_code, 200)

    def test_get_with_retries_raises_400(self):
        resp = Downloader.get_with_retries(BugzillaDownloader._URL)
        self.assertEqual(resp.status_code, 400)
