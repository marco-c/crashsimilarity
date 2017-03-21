# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

# CLI INTERFACE THAT EVALUATES THE SIMILARITY BETWEEN STACK TRACES IN A GIVEN SIGNATURE.

import download_data
import crash_similarity
import argparse
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='Test Signature Coherence')
parser.add_argument('--signature', required=True, help='Signature')
parser.add_argument('--product', required=True, help='Product for which crash data is needed to be downloaded')
parser.add_argument('--top', help='Number of top similar and different stack traces(Default 10)', default=10, type=int)
args = parser.parse_args()

if __name__ == '__main__':

    # Downloads some data (e.g. the past 7 days)
    download_data.download_crashes(days=7, product=args.product)
    paths = download_data.get_paths(days=7, product=args.product)

    # Reads the corpus
    corpus = crash_similarity.read_corpus(paths)

    # Trains the model on that data
    model = crash_similarity.train_model(corpus)

    # Evaluates the similarity between the stack traces in a given signature.
    logging.debug(args.signature + ' \n')

    similarities = crash_similarity.signature_similarity(model, paths, args.signature, args.signature)
    logging.debug('Top ' + str(args.top))
    for similarity in similarities[:args.top]:
        logging.debug(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
    logging.debug('Bottom ' + str(args.top))
    for similarity in similarities[-int(args.top):]:
        logging.debug(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
