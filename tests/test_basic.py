# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest


import crash_similarity

class BasicTest(unittest.TestCase):

    def test_pass(self):
        self.assertTrue(True)

    # Test if at the number of zero distances are at least the number of different reports when pared against itself
    def test_zero_dist_coherence(self):
		paths = ['crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']
		corpus = crash_similarity.read_corpus(paths)
		model = crash_similarity.train_model(corpus)

		signature = 'mozilla::MonitorAutoLock::MonitorAutoLock'
		print('Testing Coherence with', signature, "signarue.")
		signature_size = len(crash_similarity.get_stack_traces_for_signature(paths, signature))
		similarities = crash_similarity.signature_similarity(model, paths, signature, signature)

		for doc1, doc2, dist in similarities:
			if(doc1 != doc2):
				break;
			self.assertTrue(dist == 0)


if __name__ == '__main__':
    unittest.main()
