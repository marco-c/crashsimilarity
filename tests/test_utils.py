import unittest
from datetime import datetime
import sys
sys.path.append('../')
import utils
from download_data import get_paths


class UtilsTest(unittest.TestCase):

    url = 'https://bugzilla.mozilla.org/rest/bug'

    def test_utc_today_returns_today_date(self):
        self.assertEqual(utils.utc_today(), datetime.now().date())

    def test_get_with_retries(self):
        bug_id = '1308863'
        resp = utils.get_with_retries(self.url, params={'id': bug_id})
        self.assertEqual(resp.status_code, 200)

    def test_get_with_retries_raises_400_with_no_params(self):
        resp = utils.get_with_retries(self.url)
        self.assertEqual(resp.status_code, 400)

if __name__ == '__main__':
    unittest.main()