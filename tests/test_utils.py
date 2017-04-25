import unittest
from datetime import datetime

from crashsimilarity import utils
from crashsimilarity.utils import StackTraceProcessor


class UtilsTest(unittest.TestCase):
    def test_utc_today_returns_today_date(self):
        self.assertEqual(utils.utc_today(), datetime.utcnow().date())

    def test_read_files(self):
        paths = ['tests/test.json']
        for line in utils.read_files(paths):
            self.assertIn('proto_signature', line)
            self.assertIn('signature', line)
            self.assertIn('uuid', line)


class StackTraceProcessorTest(unittest.TestCase):
    raw_traces = ['{"proto_signature": "a | CAPITAL_LETTERS | c", "uuid": "1", "signature": "c"}',
                  '{"proto_signature": "a | b | d", "uuid": "2", "signature": "d"}',
                  '{"proto_signature": "a | x | d", "uuid": "3", "signature": "d"}',
                  '{"proto_signature": "a | b | e", "uuid": "4", "signature": "same"}',
                  '{"proto_signature": "with | name@0xAddr | drop", "uuid": "5", "signature": "drop"}',
                  '{"proto_signature": "with | xul.dll@", "uuid": "6", "signature": "ignored"}',
                  '{"proto_signature": "a | b | e", "uuid": "7", "signature": "same"}']

    expected_traces = [(['a', 'capital_letters', 'c'], 'c', '1'),
                       (['a', 'b', 'd'], 'd', '2'),
                       (['a', 'x', 'd'], 'd', '3'),
                       (['a', 'b', 'e'], 'same', '4'),
                       (['with', 'name@0x', 'drop'], 'drop', '5')]

    def test_clean_func(self):
        funcs = [('js::jit::MakeMRegExpHoistable ', 'js::jit::makemregexphoistable'),
                 (' AppKit@0x7be82f ', 'appkit@0x'),
                 (' __RtlUserThreadStart ', '__rtluserthreadstart'), (' xul.dll@0x1ade7cf ', 'xul.dll@0x'),
                 ('XUL@0x7bd20f', 'xul@0x'), ('libxul.so@0xe477b4 ', 'libxul.so@0x')]
        for f, expected in funcs:
            self.assertEqual(StackTraceProcessor._preprocess(f), [expected])

    def test_preprocess(self):
        stack_trace = 'js::GCM::pMSt | js::GCM::d | js::gc::GCR::w | JS::SIGC | CoreF@0xa74b0 | HTlb@0x312ab | AppKit@0x476cc'
        expected = ['js::gcm::pmst', 'js::gcm::d', 'js::gc::gcr::w', 'js::sigc', 'coref@0x', 'htlb@0x', 'appkit@0x']
        actual = StackTraceProcessor._preprocess(stack_trace)
        self.assertEqual(actual, expected)
        actual = StackTraceProcessor._preprocess(stack_trace, 3)
        self.assertEqual(actual, expected[:3])

    def test_process(self):
        actual = list(StackTraceProcessor.process(self.raw_traces))
        self.assertEqual(actual, self.expected_traces)
