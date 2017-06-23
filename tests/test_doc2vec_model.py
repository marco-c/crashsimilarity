import random
import unittest

from crashsimilarity.models.gensim_model_wrapper import Doc2vecModelWrapper
from crashsimilarity.models.wmd_calculator import WMDCalculator


class Doc2VecModelTest(unittest.TestCase):
    PATH = ['test.json']

    def test_WMDCalculator(self):
        model_with_corpus = Doc2vecModelWrapper.read_corpus(self.PATH).train_model()
        model, corpus = model_with_corpus.model, model_with_corpus.corpus
        calculator = WMDCalculator.build_with_all_distances(model, corpus)

        self.assertEqual(calculator.dist.shape[0], calculator.dist.shape[1])
        self.assertEqual(calculator.dist.shape[0], len(model.wv.vocab))

        random_traces = list(set([random.randint(0, len(corpus) - 1) for _ in range(50)]))
        for i in random_traces:
            for j in random_traces:
                doc1 = corpus[i].words
                doc2 = corpus[j].words
                actual_wmd = calculator.wmdistance(doc1, doc2)
                expected_wmd = model.wmdistance(doc1, doc2)
                self.assertAlmostEqual(actual_wmd, expected_wmd, places=5)
