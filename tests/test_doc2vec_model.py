import random
import unittest

import numpy as np

from crashsimilarity.models.gensim_model_wrapper import Doc2vecModelWrapper
from crashsimilarity.models.similarity.doc2vec_similarity import Doc2VecSimilarity
from crashsimilarity.models.wmd_calculator import WMDCalculator


class Doc2VecModelTest(unittest.TestCase):
    PATH = ['tests/test.json']

    @classmethod
    def setUpClass(cls):
        model_with_corpus = Doc2vecModelWrapper.read_corpus(cls.PATH).train_model()
        cls.model = model_with_corpus.model
        cls.corpus = model_with_corpus.corpus
        cls.wmd_calculator = WMDCalculator.build_with_all_distances(cls.model, cls.corpus)

    def test_WMDCalculator(self):
        self.assertEqual(self.wmd_calculator.dist.shape[0], self.wmd_calculator.dist.shape[1])
        self.assertEqual(self.wmd_calculator.dist.shape[0], len(self.model.wv.vocab))

        # test associativity
        random_traces = list(set([random.randint(0, len(self.corpus) - 1) for _ in range(10)]))
        for i in random_traces:
            for j in random_traces:
                doc1 = self.corpus[i].words
                doc2 = self.corpus[j].words
                actual1 = self.wmd_calculator.wmdistance(doc1, doc2)
                actual2 = self.wmd_calculator.wmdistance(doc2, doc1)
                expected = self.model.wmdistance(doc1, doc2)
                self.assertAlmostEqual(actual1, actual2, places=5)
                self.assertAlmostEqual(actual1, expected, places=5)

        random_traces = list(set([random.randint(0, len(self.corpus) - 1) for _ in range(50)]))
        for i in random_traces:
            for j in random_traces:
                doc1 = self.corpus[i].words
                doc2 = self.corpus[j].words
                actual_wmd = self.wmd_calculator.wmdistance(doc1, doc2)
                expected_wmd = self.model.wmdistance(doc1, doc2)
                self.assertAlmostEqual(actual_wmd, expected_wmd, places=5)

    def test_top_similar_traces(self):
        algo = Doc2VecSimilarity(self.wmd_calculator)
        target_trace = self.corpus[100].words
        expected = list(enumerate([self.wmd_calculator.wmdistance(target_trace, c.words) for c in self.corpus]))
        expected = [i[0] for i in sorted(expected, key=lambda x: x[1])[:10]]  # compare document indexes
        actual = [i[0] for i in algo.top_similar_traces(target_trace, self.corpus, 10)]
        self.assertEqual(actual, expected)

    def test_signatures_similarity(self):
        trace1 = self.corpus[100].words
        trace2 = self.corpus[42].words
        trace3 = self.corpus[123].words
        trace4 = self.corpus[201].words
        signature1 = [trace1, trace2, trace3]
        signature2 = [trace3, trace1, trace2]
        signature3 = [trace4, trace3]

        algo = Doc2VecSimilarity(self.wmd_calculator)

        my_wmd = algo._calculator.wmdistance

        actual = algo.signatures_similarity(signature1, signature2)
        self.assertTupleEqual(actual.shape, (3, 3))
        expected = [[1 / my_wmd(trace1, trace3), np.inf, 1 / my_wmd(trace1, trace2)],
                    [1 / my_wmd(trace2, trace3), 1 / my_wmd(trace2, trace1), np.inf],
                    [np.inf, 1 / my_wmd(trace3, trace1), 1 / my_wmd(trace3, trace2)]]
        self.assertListEqual(actual.tolist(), expected)

        actual = algo.signatures_similarity(signature1, signature3)
        self.assertTupleEqual(actual.shape, (3, 2))

        actual = algo.signatures_similarity(signature3, signature2)
        self.assertTupleEqual(actual.shape, (2, 3))

        actual = algo.signatures_similarity([], [])
        self.assertTupleEqual(actual.shape, (0, 0))
        self.assertListEqual(actual.tolist(), [])

    def test_signature_coherence(self):
        trace1 = self.corpus[100].words
        trace2 = self.corpus[42].words
        signature = [trace1, trace2]
        algo = Doc2VecSimilarity(self.wmd_calculator)
        actual = algo.signature_coherence(signature).tolist()
        expected = [[np.inf, 1 / self.wmd_calculator.wmdistance(trace1, trace2)],
                    [1 / self.wmd_calculator.wmdistance(trace2, trace1), np.inf]]
        self.assertListEqual(actual, expected)
