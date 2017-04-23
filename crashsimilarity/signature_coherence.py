# CLI INTERFACE THAT EVALUATES THE SIMILARITY BETWEEN STACK TRACES IN A GIVEN SIGNATURE.
from crashsimilarity import utils, crash_similarity
import sys
import argparse


def parse_args(args):
    parser = argparse.ArgumentParser(description='Test Signature Coherence')
    parser.add_argument('--signature', required=True, help='Signature')
    parser.add_argument('--product', required=True, help='Product for which crash data is needed to be downloaded')
    parser.add_argument('--top', help='Number of top similar and different stack traces(Default 10)', default=10, type=int)
    return parser.parse_args(args)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    # Downloads some data (e.g. the past 7 days)
    utils.download_crashes(days=7, product=args.product)
    paths = utils.get_paths(days=7, product=args.product)

    # Reads the corpus
    corpus = crash_similarity.read_corpus(paths)

    # Trains the model on that data
    model = crash_similarity.train_model(corpus)

    # Evaluates the similarity between the stack traces in a given signature.
    print(args.signature + ' \n')

    similarities = crash_similarity.signature_similarity(model, paths, args.signature, args.signature)
    print('Top ' + str(args.top))
    for similarity in similarities[:args.top]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
    print('Bottom ' + str(args.top))
    for similarity in similarities[-int(args.top):]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
