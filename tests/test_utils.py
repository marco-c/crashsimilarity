import unittest
from datetime import datetime

from crashsimilarity import utils


class UtilsTest(unittest.TestCase):
    def test_utc_today_returns_today_date(self):
        self.assertEqual(utils.utc_today(), datetime.utcnow().date())

    def test_read_files(self):
        paths = ['tests/test.json']
        for line in utils.read_files(paths):
            self.assertIn('proto_signature', line)
            self.assertIn('signature', line)
            self.assertIn('uuid', line)
