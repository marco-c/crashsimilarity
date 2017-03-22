# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest


import crash_similarity


class CrashSimilarityTest(unittest.TestCase):

    # Train Model to be used in all tests
    @classmethod
    def setUpClass(self):
        self.paths = ['tests/test.json']
        self.corpus = crash_similarity.read_corpus(self.paths)
        self.model = crash_similarity.train_model(self.corpus)

        print('Model Trained with paths:\n{}'.format(self.paths))

    #test if equal reports have distance 0 and different reports have difference greater than 0
    def test_zero_dist_coherence(self):
        signature = 'mozilla::testZeroCoherence'
        print('\nTesting Coherence with {} signature.'.format(signature))

        similarities = crash_similarity.signature_similarity(self.model, self.paths, signature, signature)

        errors = []
        for doc1, doc2, dist in similarities:
            if doc1 != doc2:
                try:
                    self.assertTrue(dist > 0)
                except AssertionError as e:
                    errors.append((doc1, doc2, dist))
            else:
                try:
                    self.assertEqual(dist, 0)
                except AssertionError as e:
                    errors.append((doc1, doc2, dist))

        print('Number of errors:{}'.format(len(errors)))
        for e in errors:
            print('doc1: {}\ndoc2: {}\ndist: {}'.format(e[0], e[1], e[2]))
        self.assertEqual(len(errors), 0)

    # Test if reports with the same words in different order have distance different than zero
    def test_order_similarity(self):
        print('\nTesting if order changes document similarity.')

        signature1 = 'mozilla::testOrdem1'
        signature2 = 'mozilla::testOrdem2'
        signature3 = 'mozilla::testOrdem3'

        similarity_mid = crash_similarity.signature_similarity(self.model, self.paths, signature1, signature2)
        similarity_end = crash_similarity.signature_similarity(self.model, self.paths, signature1, signature3)

        doc_mid1, doc_mid2, dist_mid = similarity_mid[0]
        doc_end1, doc_end2, dist_end = similarity_end[0]

        if dist_mid >= dist_end:
            print('{}\n{}\n{}'.format(doc_mid1, doc_mid2, dist_mid))
            print('{}\n{}\n{}'.format(doc_end1, doc_end2, dist_end))

        self.assertTrue(dist_mid < dist_end)
        print('\n')


if __name__ == '__main__':
    unittest.main()
