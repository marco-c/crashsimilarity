import unittest
import multiprocessing
import os
from pathlib import Path
import numpy as np

from crashsimilarity.stacktrace import StackTraceProcessor
from crashsimilarity.models import doc2vec, word2vec


class CrashSimilarityTest(unittest.TestCase):
    # Train Model to be used in all tests
    @classmethod
    def setUpClass(self):
        current_abs_path = os.path.abspath(os.path.dirname(__file__))
        project_abs_path = Path(current_abs_path).parent
        self.paths = [os.path.join(project_abs_path, 'tests/test.json')]
        self.doc2vec_model = doc2vec.Doc2Vec(self.paths)
        self.doc2vec_trained_model = self.doc2vec_model.get_model()
        self.doc2vec_trained_model.init_sims(replace=True)
        self.word2vec_model = word2vec.Word2Vec(self.paths)
        self.word2vec_trained_model = self.word2vec_model.get_model()
        self.word2vec_trained_model.init_sims(replace=True)

    # Test if equal reports have distance 0 and different reports have difference greater than 0
    def zero_dist_coherence(self, model):
        signature = 'mozilla::testZeroCoherence'

        similarities = model.signature_similarity(self.paths, signature, signature)

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

    def test_zero_dist_coherence(self):
        self.zero_dist_coherence(self.doc2vec_model)
        self.zero_dist_coherence(self.word2vec_model)

    # Test if reports with the same words in different order have distance different than zero

    def order_similarity(self, model):

        signature1 = 'mozilla::testOrdem1'
        signature2 = 'mozilla::testOrdem2'
        signature3 = 'mozilla::testOrdem3'

        similarity_mid = model.signature_similarity(self.paths, signature1, signature2)
        similarity_end = model.signature_similarity(self.paths, signature1, signature3)

        doc_mid1, doc_mid2, dist_mid = similarity_mid[0]
        doc_end1, doc_end2, dist_end = similarity_end[0]

        self.assertTrue(dist_mid < dist_end)

    @unittest.expectedFailure
    def test_order_similarity(self):
        self.order_similarity(self.doc2vec_model)
        self.order_similarity(self.word2vec_model)

    def wmdistance_cosine_non_zero_distance(self, model, trained_model):
        doc1 = "KiFastSystemCallRet | NtWaitForMultipleObjects | WaitForMultipleObjectsEx | RealMsgWaitForMultipleObjectsEx | CCliModalLoop::BlockFn | CoWaitForMultipleHandles | mozilla::ipc::MessageChannel::WaitForSyncNotifyWithA11yReentry | mozilla::ipc::MessageChannel::WaitForSyncNotify | mozilla::ipc::MessageChannel::Send | mozilla::dom::PScreenManagerChild::SendScreenRefresh | mozilla::widget::ScreenProxy::EnsureCacheIsValid | mozilla::widget::ScreenProxy::GetColorDepth | gfxPlatform::PopulateScreenInfo | gfxPlatform::Init | mozilla::dom::ContentProcess::Init | XRE_InitChildProcess | content_process_main | wmain | remainder | remainder | WinSqmStartSession | _SEH_epilog4 | WinSqmStartSession | _RtlUserThreadStart"
        doc2 = "Assertion::~Assertion | Assertion::Destroy | InMemoryDataSource::DeleteForwardArcsEntry | PL_DHashTableEnumerate | InMemoryDataSource::~InMemoryDataSource | InMemoryDataSource::`vector deleting destructor' | InMemoryDataSource::Internal::Release | InMemoryDataSource::Release | nsCOMPtr_base::~nsCOMPtr_base | RDFXMLDataSourceImpl::`vector deleting destructor' | RDFXMLDataSourceImpl::Release | DoDeferredRelease<T> | XPCJSRuntime::GCCallback | Collect | js::GC | js::GCForReason | nsXPConnect::Collect | nsCycleCollector::GCIfNeeded | nsCycleCollector::Collect | nsCycleCollector::Shutdown | nsCycleCollector_shutdown | mozilla::ShutdownXPCOM | ScopedXPCOMStartup::~ScopedXPCOMStartup | XREMain::XRE_main | XRE_main | wmain | __tmainCRTStartup | BaseThreadInitThunk | __RtlUserThreadStart | _RtlUserThreadStart"

        words_to_test1 = StackTraceProcessor.preprocess(doc1)
        words_to_test_clean1 = [w for w in np.unique(words_to_test1).tolist() if w in trained_model.wv.vocab]

        words_to_test2 = StackTraceProcessor.preprocess(doc2)
        words_to_test_clean2 = [w for w in np.unique(words_to_test2).tolist() if w in trained_model.wv.vocab]

        if model.get_model_name() == 'Word2Vec':
            all_distances = np.array(1.0 - np.dot(trained_model.wv.vectors_norm, trained_model.wv.vectors_norm[
                [trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)
        else:
            all_distances = np.array(1.0 - np.dot(trained_model.wv.vectors, trained_model.wv.vectors[
                [trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)

        distance = model.wmdistance(words_to_test_clean1, words_to_test_clean2, all_distances)
        self.assertNotEqual(float('inf'), distance)

    def wmdistance_cosine_zero_distance(self, model, trained_model):
        doc1 = "A | A | A"
        doc2 = "A | A | A"

        words_to_test1 = StackTraceProcessor.preprocess(doc1)
        words_to_test_clean1 = [w for w in np.unique(words_to_test1).tolist() if w in trained_model.wv.vocab]

        words_to_test2 = StackTraceProcessor.preprocess(doc2)
        words_to_test_clean2 = [w for w in np.unique(words_to_test2).tolist() if w in trained_model.wv.vocab]

        if model.get_model_name() == 'Word2Vec':
            all_distances = np.array(1.0 - np.dot(trained_model.wv.vectors_norm, trained_model.wv.vectors_norm[
                [trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)
        else:
            all_distances = np.array(1.0 - np.dot(trained_model.wv.vectors, trained_model.wv.vectors[
                [trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)

        distance = model.wmdistance(words_to_test_clean1, words_to_test_clean2, all_distances)

        self.assertEqual(float('inf'), distance)

    def wmdistance_euclidean_non_zero_distance(self, model, trained_model):
        doc1 = "KiFastSystemCallRet | NtWaitForMultipleObjects | WaitForMultipleObjectsEx | RealMsgWaitForMultipleObjectsEx | CCliModalLoop::BlockFn | CoWaitForMultipleHandles | mozilla::ipc::MessageChannel::WaitForSyncNotifyWithA11yReentry | mozilla::ipc::MessageChannel::WaitForSyncNotify | mozilla::ipc::MessageChannel::Send | mozilla::dom::PScreenManagerChild::SendScreenRefresh | mozilla::widget::ScreenProxy::EnsureCacheIsValid | mozilla::widget::ScreenProxy::GetColorDepth | gfxPlatform::PopulateScreenInfo | gfxPlatform::Init | mozilla::dom::ContentProcess::Init | XRE_InitChildProcess | content_process_main | wmain | remainder | remainder | WinSqmStartSession | _SEH_epilog4 | WinSqmStartSession | _RtlUserThreadStart"
        doc2 = "Assertion::~Assertion | Assertion::Destroy | InMemoryDataSource::DeleteForwardArcsEntry | PL_DHashTableEnumerate | InMemoryDataSource::~InMemoryDataSource | InMemoryDataSource::`vector deleting destructor' | InMemoryDataSource::Internal::Release | InMemoryDataSource::Release | nsCOMPtr_base::~nsCOMPtr_base | RDFXMLDataSourceImpl::`vector deleting destructor' | RDFXMLDataSourceImpl::Release | DoDeferredRelease<T> | XPCJSRuntime::GCCallback | Collect | js::GC | js::GCForReason | nsXPConnect::Collect | nsCycleCollector::GCIfNeeded | nsCycleCollector::Collect | nsCycleCollector::Shutdown | nsCycleCollector_shutdown | mozilla::ShutdownXPCOM | ScopedXPCOMStartup::~ScopedXPCOMStartup | XREMain::XRE_main | XRE_main | wmain | __tmainCRTStartup | BaseThreadInitThunk | __RtlUserThreadStart | _RtlUserThreadStart"

        words_to_test1 = StackTraceProcessor.preprocess(doc1)
        words_to_test_clean1 = [w for w in np.unique(words_to_test1).tolist() if w in trained_model.wv.vocab]

        words_to_test2 = StackTraceProcessor.preprocess(doc2)
        words_to_test_clean2 = [w for w in np.unique(words_to_test2).tolist() if w in trained_model.wv.vocab]

        if model.get_model_name() == 'Word2Vec':
            all_distances = np.array(1.0 - np.dot(trained_model.wv.vectors_norm, trained_model.wv.vectors_norm[
                [trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)
        else:
            all_distances = np.array(1.0 - np.dot(trained_model.wv.vectors, trained_model.wv.vectors[
                [trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)

        distance = model.wmdistance(words_to_test_clean1, words_to_test_clean2, all_distances, distance_metric='euclidean')
        self.assertNotEqual(float('inf'), distance)

    def wmdistance_euclidean_zero_distance(self, model, trained_model):
        doc1 = "A | A | A"
        doc2 = "A | A | A"

        words_to_test1 = StackTraceProcessor.preprocess(doc1)
        words_to_test_clean1 = [w for w in np.unique(words_to_test1).tolist() if w in trained_model.wv.vocab]

        words_to_test2 = StackTraceProcessor.preprocess(doc2)
        words_to_test_clean2 = [w for w in np.unique(words_to_test2).tolist() if w in trained_model.wv.vocab]

        if model.get_model_name() == 'Word2Vec':
            all_distances = np.array(1.0 - np.dot(trained_model.wv.vectors_norm, trained_model.wv.vectors_norm[
                [trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)
        else:
            all_distances = np.array(1.0 - np.dot(trained_model.wv.vectors, trained_model.wv.vectors[
                [trained_model.wv.vocab[word].index for word in words_to_test_clean1]].transpose()), dtype=np.double)

        distance = model.wmdistance(words_to_test_clean1, words_to_test_clean2, all_distances, distance_metric='euclidean')
        self.assertEqual(float('inf'), distance)

    def test_wmdistance(self):
        self.wmdistance_cosine_non_zero_distance(self.doc2vec_model, self.doc2vec_trained_model)
        self.wmdistance_cosine_non_zero_distance(self.word2vec_model, self.word2vec_trained_model)

        self.wmdistance_cosine_zero_distance(self.doc2vec_model, self.doc2vec_trained_model)
        self.wmdistance_cosine_zero_distance(self.word2vec_model, self.word2vec_trained_model)

        self.wmdistance_euclidean_non_zero_distance(self.doc2vec_model, self.doc2vec_trained_model)
        self.wmdistance_euclidean_non_zero_distance(self.word2vec_model, self.word2vec_trained_model)

        self.wmdistance_euclidean_zero_distance(self.doc2vec_model, self.doc2vec_trained_model)
        self.wmdistance_euclidean_zero_distance(self.word2vec_model, self.word2vec_trained_model)

    def read_corpus(self, model):
        resp = model._read_corpus()
        self.assertEqual(type(resp), list)
        self.assertEqual(len(resp), 378)

    def test_read_corpus(self):
        self.read_corpus(self.doc2vec_model)
        self.read_corpus(self.word2vec_model)

    def train_model(self, model):
        resp = model._train_model()
        try:
            workers = multiprocessing.cpu_count()
        except NotImplementedError:
            workers = 2
        self.assertEqual(workers, resp.workers)
        self.assertEqual(8, resp.window)
        self.assertEqual(20, resp.epochs)
        self.assertEqual(101, len(resp.wv.vocab))

    def test_train_model(self):
        self.train_model(self.doc2vec_model)
        self.train_model(self.word2vec_model)
