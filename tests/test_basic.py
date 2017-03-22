# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest


import crash_similarity


class BasicTest(unittest.TestCase):

    # Train Model to be used in all tests
    paths = ['crashsimilarity_data/test.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']

    corpus = crash_similarity.read_corpus(paths)

    model = crash_similarity.train_model(corpus)
    print('Model Trained with paths:\n{}'.format(paths))

    def test_train_model(self):
        self.assertTrue(True)

    # Test if at the number of zero distances are at least the number of different reports when pared against itself
    def test_zero_dist_coherence(self):
        signature = 'mozilla::testZeroCoherence'
        print('\nTesting Coherence with {} signature.'.format(signature))

        similarities = crash_similarity.signature_similarity(self.__class__.model, self.__class__.paths, signature, signature)

        error = []
        for doc1, doc2, dist in similarities:
            if doc1 != doc2:
                try:
                    self.assertTrue(dist != 0)
                except AssertionError as e:
                    error.append((doc1, doc2, dist))
            else:
                try:
                    self.assertEqual(dist, 0)
                except AssertionError as e:
                    error.append((doc1, doc2, dist))

        print('Number of errors:{}'.format(len(error)))
        for e in error:
            print('doc1: {}\ndoc2: {}\ndist: {}'.format(e[0], e[1], e[2]))
        self.assertEqual(len(error), 0)

    # Test if reports with the same words in different order have distance different than zero
    def test_order_similarity(self):
        print('\nTesting if order changes document similarity.')

        signature1 = 'mozilla::testOrdem1'
        signature2 = 'mozilla::testOrdem2'
        signature3 = 'mozilla::testOrdem3'

        similarity_mid = crash_similarity.signature_similarity(self.__class__.model, self.__class__.paths, signature1, signature2)
        similarity_end = crash_similarity.signature_similarity(self.__class__.model, self.__class__.paths, signature1, signature3)

        doc_mid1, doc_mid2, dist_mid = similarity_mid[0]
        doc_end1, doc_end2, dist_end = similarity_end[0]

        print('{}\n{}\n{}'.format(doc_mid1, doc_mid2, dist_mid))
        print('{}\n{}\n{}'.format(doc_end1, doc_end2, dist_end))

        self.assertTrue(dist_mid < dist_end)
        print('\n')


if __name__ == '__main__':
    unittest.main()
