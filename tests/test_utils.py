import utils
import unittest
from datetime import datetime


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

    def test_read_files(self):
        paths = ['tests/test_utils.json']
        for line in utils.read_files(paths):
            assert 'proto_signature' in line
            assert 'signature' in line
            assert 'uuid' in line


if __name__ == '__main__':
    unittest.main()
