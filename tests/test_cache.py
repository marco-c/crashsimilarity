import unittest

from crashsimilarity.cache import Cache


class TestCache(unittest.TestCase):
    def test_build(self):
        lines = ['{"proto_signature": "a | CAPITAL_LETTERS | c", "uuid": "1", "signature": "c"}',
                 '{"proto_signature": "a | b | d", "uuid": "2", "signature": "d"}',
                 '{"proto_signature": "a | x | d", "uuid": "3", "signature": "d"}',
                 '{"proto_signature": "a | b | e", "uuid": "4", "signature": "same"}',
                 '{"proto_signature": "with | @0x end | drop", "uuid": "5", "signature": "drop"}',
                 '{"proto_signature": "with | xul.dll@", "uuid": "6", "signature": "ignored"}',
                 '{"proto_signature": "a | b | e", "uuid": "7", "signature": "same"}']
        cache = Cache.build(lines)
        self.assertEqual(cache.downloader_cache, dict())
        expected = [(['a', 'capital_letters', 'c'], 'c', '1'),
                    (['a', 'b', 'd'], 'd', '2'),
                    (['a', 'x', 'd'], 'd', '3'),
                    (['a', 'b', 'e'], 'same', '4'),
                    (['with', '@0x', 'drop'], 'drop', '5')]
        self.assertEqual(cache.traces, expected)


if __name__ == '__main__':
    unittest.main()
