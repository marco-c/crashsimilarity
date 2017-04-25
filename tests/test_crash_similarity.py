import json
import multiprocessing
import unittest

import requests_mock

from crashsimilarity import crash_similarity, utils


class CrashSimilarityTest(unittest.TestCase):
    # Train Model to be used in all tests
    @classmethod
    def setUpClass(self):
        self.paths = ['tests/test.json']
        self.corpus = crash_similarity.read_corpus(self.paths)
        self.model = crash_similarity.train_model(self.corpus)

    # Test if equal reports have distance 0 and different reports have difference greater than 0
    @unittest.expectedFailure
    def test_zero_dist_coherence(self):
        signature = 'mozilla::testZeroCoherence'

        similarities = crash_similarity.signature_similarity(self.model, self.paths, signature, signature)

        errors = []
        for doc1, doc2, dist in similarities:
            if doc1 != doc2:
                try:
                    self.assertTrue(dist > 0)
                except AssertionError:
                    errors.append((doc1, doc2, dist))
            else:
                try:
                    self.assertEqual(dist, 0)
                except AssertionError:
                    errors.append((doc1, doc2, dist))

        self.assertEqual(len(errors), 0)

    # Test if reports with the same words in different order have distance different than zero
    @unittest.expectedFailure
    def test_order_similarity(self):

        signature1 = 'mozilla::testOrdem1'
        signature2 = 'mozilla::testOrdem2'
        signature3 = 'mozilla::testOrdem3'

        similarity_mid = crash_similarity.signature_similarity(self.model, self.paths, signature1, signature2)
        similarity_end = crash_similarity.signature_similarity(self.model, self.paths, signature1, signature3)

        doc_mid1, doc_mid2, dist_mid = similarity_mid[0]
        doc_end1, doc_end2, dist_end = similarity_end[0]

        self.assertTrue(dist_mid < dist_end)

    def test_read_corpus(self):
        resp = crash_similarity.read_corpus(self.paths)
        self.assertEqual(type(resp), list)
        self.assertEqual(len(resp), 378)

    def test_get_stack_traces_for_signature(self):
        signature = 'js::GCMarker::processMarkStackTop'
        resp = crash_similarity.get_stack_traces_for_signature(self.paths, signature)
        for line in utils.read_files(self.paths):
            data = json.loads(line)
            if data['signature'] == signature:
                assert data['proto_signature'] in resp

    def test_get_stack_trace_for_uuid(self):
        proto_signature = 'js::GCMarker::processMarkStackTop | js::GCMarker::drainMarkStack | js::gc::GCRuntime::incrementalCollectSlice | js::gc::GCRuntime::gcCycle | js::gc::GCRuntime::collect | JS::StartIncrementalGC | nsJSContext::GarbageCollectNow | nsTimerImpl::Fire | nsTimerEvent::Run | nsThread::ProcessNextEvent | NS_ProcessPendingEvents | nsBaseAppShell::NativeEventCallback | nsAppShell::ProcessGeckoEvents | CoreFoundation@0xa74b0 | CoreFoundation@0x8861c | CoreFoundation@0x87b15 | CoreFoundation@0x87513 | HIToolbox@0x312ab | HIToolbox@0x310e0 | HIToolbox@0x30f15 | AppKit@0x476cc | AppKit@0x7be82f | CoreFoundation@0x9e3a1 | AppKit@0xc56609 | AppKit@0xc9e7f7 | AppKit@0xc9e387 | AppKit@0xc567a9 | AppKit@0xc5867b | AppKit@0xc57ccc | AppKit@0xc5a9c2 | AppKit@0x47c2ed | AppKit@0x47c304 | AppKit@0xcdcf03 | AppKit@0xc56e2b | AppKit@0xc579af | AppKit@0xcdcee2 | AppKit@0xc5e77b | AppKit@0xc9897a | AppKit@0xc9c88c | AppKit@0xc7f10e'
        uuid = '90dcebb6-f711-4a8b-9e68-5abf72161109'
        with requests_mock.Mocker() as m:
            m.get('https://crash-stats.mozilla.com/api/ProcessedCrash', json={'proto_signature': proto_signature})
            resp = crash_similarity.get_stack_trace_for_uuid(uuid)
            self.assertEqual(resp, proto_signature)

    def test_train_model(self):
        resp = crash_similarity.train_model(self.corpus)
        try:
            workers = multiprocessing.cpu_count()
        except:
            workers = 2
        self.assertEqual(workers, resp.workers)
        self.assertEqual(8, resp.window)
        self.assertEqual(20, resp.iter)
        self.assertEqual(101, len(resp.wv.vocab))


if __name__ == '__main__':
    unittest.main()
