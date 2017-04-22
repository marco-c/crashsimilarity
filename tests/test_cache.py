import unittest

from crashsimilarity.cache import TracesCache


class TestCache(unittest.TestCase):
    def test_traces_cache_build(self):
        lines = ['{"proto_signature": "a | CAPITAL_LETTERS | c", "uuid": "1", "signature": "c"}',
                 '{"proto_signature": "a | b | d", "uuid": "2", "signature": "d"}',
                 '{"proto_signature": "a | x | d", "uuid": "3", "signature": "d"}',
                 '{"proto_signature": "a | b | e", "uuid": "4", "signature": "same"}',
                 '{"proto_signature": "with | @0x end | drop", "uuid": "5", "signature": "drop"}',
                 '{"proto_signature": "with | xul.dll@", "uuid": "6", "signature": "ignored"}',
                 '{"proto_signature": "a | b | e", "uuid": "7", "signature": "same"}']
        cache = TracesCache().build(lines)
        expected = [(['a', 'capital_letters', 'c'], 'c', '1'),
                    (['a', 'b', 'd'], 'd', '2'),
                    (['a', 'x', 'd'], 'd', '3'),
                    (['a', 'b', 'e'], 'same', '4'),
                    (['with', '@0x', 'drop'], 'drop', '5')]
        self.assertEqual(cache.traces, expected)
