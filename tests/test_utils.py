import unittest
import requests_mock
import json
from datetime import datetime

from crashsimilarity import utils
from crashsimilarity.stacktrace import StackTracesGetter, StackTraceProcessor


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

    expected_traces = [(['a', 'capital_letters', 'c'], 'c'),
                       (['a', 'b', 'd'], 'd'),
                       (['a', 'x', 'd'], 'd'),
                       (['a', 'b', 'e'], 'same'),
                       (['with', 'name@0x', 'drop'], 'drop')]

    def test_clean_func(self):
        funcs = [('js::jit::MakeMRegExpHoistable ', 'js::jit::makemregexphoistable'),
                 (' AppKit@0x7be82f ', 'appkit@0x'),
                 (' __RtlUserThreadStart ', '__rtluserthreadstart'), (' xul.dll@0x1ade7cf ', 'xul.dll@0x'),
                 ('XUL@0x7bd20f', 'xul@0x'), ('libxul.so@0xe477b4 ', 'libxul.so@0x')]
        for f, expected in funcs:
            self.assertEqual(StackTraceProcessor.preprocess(f), [expected])

    def test_preprocess(self):
        stack_trace = 'js::GCM::pMSt | js::GCM::d | js::gc::GCR::w | JS::SIGC | CoreF@0xa74b0 | HTlb@0x312ab | AppKit@0x476cc'
        expected = ['js::gcm::pmst', 'js::gcm::d', 'js::gc::gcr::w', 'js::sigc', 'coref@0x', 'htlb@0x', 'appkit@0x']
        actual = StackTraceProcessor.preprocess(stack_trace)
        self.assertEqual(actual, expected)
        actual = StackTraceProcessor.preprocess(stack_trace, 3)
        self.assertEqual(actual, expected[:3])

    def test_process(self):
        actual = list(StackTraceProcessor.process(self.raw_traces))
        self.assertEqual(actual, self.expected_traces)


class StackTracesGetterTest(unittest.TestCase):
    paths = ['tests/test.json']

    def test_get_stack_traces_for_signature(self):
        signature = 'js::GCMarker::processMarkStackTop'
        resp = StackTracesGetter.get_stack_traces_for_signature(self.paths, signature)
        for line in utils.read_files(self.paths):
            data = json.loads(line)
            if data['signature'] == signature:
                assert data['proto_signature'] in resp

    def test_get_stack_trace_for_uuid(self):
        proto_signature = 'js::GCMarker::processMarkStackTop | js::GCMarker::drainMarkStack | js::gc::GCRuntime::incrementalCollectSlice | js::gc::GCRuntime::gcCycle | js::gc::GCRuntime::collect | JS::StartIncrementalGC | nsJSContext::GarbageCollectNow | nsTimerImpl::Fire | nsTimerEvent::Run | nsThread::ProcessNextEvent | NS_ProcessPendingEvents | nsBaseAppShell::NativeEventCallback | nsAppShell::ProcessGeckoEvents | CoreFoundation@0xa74b0 | CoreFoundation@0x8861c | CoreFoundation@0x87b15 | CoreFoundation@0x87513 | HIToolbox@0x312ab | HIToolbox@0x310e0 | HIToolbox@0x30f15 | AppKit@0x476cc | AppKit@0x7be82f | CoreFoundation@0x9e3a1 | AppKit@0xc56609 | AppKit@0xc9e7f7 | AppKit@0xc9e387 | AppKit@0xc567a9 | AppKit@0xc5867b | AppKit@0xc57ccc | AppKit@0xc5a9c2 | AppKit@0x47c2ed | AppKit@0x47c304 | AppKit@0xcdcf03 | AppKit@0xc56e2b | AppKit@0xc579af | AppKit@0xcdcee2 | AppKit@0xc5e77b | AppKit@0xc9897a | AppKit@0xc9c88c | AppKit@0xc7f10e'
        uuid = '90dcebb6-f711-4a8b-9e68-5abf72161109'
        with requests_mock.Mocker() as m:
            m.get('https://crash-stats.mozilla.com/api/ProcessedCrash', json={'proto_signature': proto_signature})
            resp = StackTracesGetter.get_stack_trace_for_uuid(uuid)
            self.assertEqual(resp, proto_signature)
