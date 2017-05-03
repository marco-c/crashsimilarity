import multiprocessing
import unittest
import numpy as np

from crashsimilarity import utils
from crashsimilarity.models import doc2vec


class CrashSimilarityTest(unittest.TestCase):
    # Train Model to be used in all tests
    @classmethod
    def setUpClass(self):
        self.paths = ['tests/test.json']
        self.model = doc2vec.Doc2Vec(self.paths)
        self.trained_model = self.model.get_model()

    # Test if equal reports have distance 0 and different reports have difference greater than 0
    def test_zero_dist_coherence(self):
        signature = 'mozilla::testZeroCoherence'

        similarities = self.model.signature_similarity(self.paths, signature, signature)

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

        similarity_mid = self.model.signature_similarity(self.paths, signature1, signature2)
        similarity_end = self.model.signature_similarity(self.paths, signature1, signature3)

        doc_mid1, doc_mid2, dist_mid = similarity_mid[0]
        doc_end1, doc_end2, dist_end = similarity_end[0]

        self.assertTrue(dist_mid < dist_end)

    def test_wmdistance_cosine_non_zero_distance(self):
        doc1 = "KiFastSystemCallRet | NtWaitForMultipleObjects | WaitForMultipleObjectsEx | RealMsgWaitForMultipleObjectsEx | CCliModalLoop::BlockFn | CoWaitForMultipleHandles | mozilla::ipc::MessageChannel::WaitForSyncNotifyWithA11yReentry | mozilla::ipc::MessageChannel::WaitForSyncNotify | mozilla::ipc::MessageChannel::Send | mozilla::dom::PScreenManagerChild::SendScreenRefresh | mozilla::widget::ScreenProxy::EnsureCacheIsValid | mozilla::widget::ScreenProxy::GetColorDepth | gfxPlatform::PopulateScreenInfo | gfxPlatform::Init | mozilla::dom::ContentProcess::Init | XRE_InitChildProcess | content_process_main | wmain | remainder | remainder | WinSqmStartSession | _SEH_epilog4 | WinSqmStartSession | _RtlUserThreadStart"
        doc2 = "Assertion::~Assertion | Assertion::Destroy | InMemoryDataSource::DeleteForwardArcsEntry | PL_DHashTableEnumerate | InMemoryDataSource::~InMemoryDataSource | InMemoryDataSource::`vector deleting destructor' | InMemoryDataSource::Internal::Release | InMemoryDataSource::Release | nsCOMPtr_base::~nsCOMPtr_base | RDFXMLDataSourceImpl::`vector deleting destructor' | RDFXMLDataSourceImpl::Release | DoDeferredRelease<T> | XPCJSRuntime::GCCallback | Collect | js::GC | js::GCForReason | nsXPConnect::Collect | nsCycleCollector::GCIfNeeded | nsCycleCollector::Collect | nsCycleCollector::Shutdown | nsCycleCollector_shutdown | mozilla::ShutdownXPCOM | ScopedXPCOMStartup::~ScopedXPCOMStartup | XREMain::XRE_main | XRE_main | wmain | __tmainCRTStartup | BaseThreadInitThunk | __RtlUserThreadStart | _RtlUserThreadStart"

        words_to_test1 = utils.StackTraceProcessor.preprocess(doc1)
        words_to_test_clean1 = [w for w in np.unique(words_to_test1).tolist() if w in self.trained_model]

        words_to_test2 = utils.StackTraceProcessor.preprocess(doc2)
        words_to_test_clean2 = [w for w in np.unique(words_to_test2).tolist() if w in self.trained_model]

        all_distances = np.array(1.0 - np.dot(self.trained_model.wv.syn0norm, self.trained_model.wv.syn0norm[
            [self.trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)

        distance = self.model.wmdistance(words_to_test_clean1, words_to_test_clean2, all_distances)
        self.assertNotEqual(float('inf'), distance)

    def test_wmdistance_cosine_zero_distance(self):
        doc1 = "A | A | A"
        doc2 = "A | A | A"

        words_to_test1 = utils.StackTraceProcessor.preprocess(doc1)
        words_to_test_clean1 = [w for w in np.unique(words_to_test1).tolist() if w in self.trained_model]

        words_to_test2 = utils.StackTraceProcessor.preprocess(doc2)
        words_to_test_clean2 = [w for w in np.unique(words_to_test2).tolist() if w in self.trained_model]

        all_distances = np.array(1.0 - np.dot(self.trained_model.wv.syn0norm, self.trained_model.wv.syn0norm[
            [self.trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)

        distance = self.model.wmdistance(words_to_test_clean1, words_to_test_clean2, all_distances)

        self.assertEqual(float('inf'), distance)

    def test_wmdistance_euclidean_non_zero_distance(self):
        doc1 = "KiFastSystemCallRet | NtWaitForMultipleObjects | WaitForMultipleObjectsEx | RealMsgWaitForMultipleObjectsEx | CCliModalLoop::BlockFn | CoWaitForMultipleHandles | mozilla::ipc::MessageChannel::WaitForSyncNotifyWithA11yReentry | mozilla::ipc::MessageChannel::WaitForSyncNotify | mozilla::ipc::MessageChannel::Send | mozilla::dom::PScreenManagerChild::SendScreenRefresh | mozilla::widget::ScreenProxy::EnsureCacheIsValid | mozilla::widget::ScreenProxy::GetColorDepth | gfxPlatform::PopulateScreenInfo | gfxPlatform::Init | mozilla::dom::ContentProcess::Init | XRE_InitChildProcess | content_process_main | wmain | remainder | remainder | WinSqmStartSession | _SEH_epilog4 | WinSqmStartSession | _RtlUserThreadStart"
        doc2 = "Assertion::~Assertion | Assertion::Destroy | InMemoryDataSource::DeleteForwardArcsEntry | PL_DHashTableEnumerate | InMemoryDataSource::~InMemoryDataSource | InMemoryDataSource::`vector deleting destructor' | InMemoryDataSource::Internal::Release | InMemoryDataSource::Release | nsCOMPtr_base::~nsCOMPtr_base | RDFXMLDataSourceImpl::`vector deleting destructor' | RDFXMLDataSourceImpl::Release | DoDeferredRelease<T> | XPCJSRuntime::GCCallback | Collect | js::GC | js::GCForReason | nsXPConnect::Collect | nsCycleCollector::GCIfNeeded | nsCycleCollector::Collect | nsCycleCollector::Shutdown | nsCycleCollector_shutdown | mozilla::ShutdownXPCOM | ScopedXPCOMStartup::~ScopedXPCOMStartup | XREMain::XRE_main | XRE_main | wmain | __tmainCRTStartup | BaseThreadInitThunk | __RtlUserThreadStart | _RtlUserThreadStart"

        words_to_test1 = utils.StackTraceProcessor.preprocess(doc1)
        words_to_test_clean1 = [w for w in np.unique(words_to_test1).tolist() if w in self.trained_model]

        words_to_test2 = utils.StackTraceProcessor.preprocess(doc2)
        words_to_test_clean2 = [w for w in np.unique(words_to_test2).tolist() if w in self.trained_model]

        all_distances = np.array(1.0 - np.dot(self.trained_model.wv.syn0norm, self.trained_model.wv.syn0norm[
            [self.trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)

        distance = self.model.wmdistance(words_to_test_clean1, words_to_test_clean2, all_distances, distance_metric='euclidean')
        self.assertNotEqual(float('inf'), distance)

    def test_wmdistance_euclidean_zero_distance(self):
        doc1 = "A | A | A"
        doc2 = "A | A | A"

        words_to_test1 = utils.StackTraceProcessor.preprocess(doc1)
        words_to_test_clean1 = [w for w in np.unique(words_to_test1).tolist() if w in self.trained_model]

        words_to_test2 = utils.StackTraceProcessor.preprocess(doc2)
        words_to_test_clean2 = [w for w in np.unique(words_to_test2).tolist() if w in self.trained_model]

        all_distances = np.array(1.0 - np.dot(self.trained_model.wv.syn0norm, self.trained_model.wv.syn0norm[
            [self.trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)

        distance = self.model.wmdistance(words_to_test_clean1, words_to_test_clean2, all_distances, distance_metric='euclidean')
        self.assertEqual(float('inf'), distance)

    def test_read_corpus(self):
        resp = self.model._read_corpus()
        self.assertEqual(type(resp), list)
        self.assertEqual(len(resp), 378)

    def test_train_model(self):
        resp = self.model._train_model()
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
