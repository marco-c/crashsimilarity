import random
import unittest

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
        self.assertEquals(actual, expected)
