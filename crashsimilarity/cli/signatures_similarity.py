import pprint

from crashsimilarity.downloader import SocorroDownloader
import argparse
import sys

from crashsimilarity.models.gensim_model_wrapper import Doc2vecModelWrapper
from crashsimilarity.models.similarity.doc2vec_similarity import Doc2VecSimilarity
from crashsimilarity.models.wmd_calculator import WMDCalculator
from crashsimilarity.utils import StackTracesGetter


def parse_args(args):
    parser = argparse.ArgumentParser(description='Test similarities between two signatures')
    parser.add_argument('-1', '--one', required=True, help='First signature')
    parser.add_argument('-2', '--two', required=True, help='Second signature')
    parser.add_argument('-p', '--product', required=True, help='Product for which crash data is needed to be downloaded')
    parser.add_argument('-t', '--top', help='Number of top similar and different stack traces(Default 10)', default=10, type=int)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    SocorroDownloader.download_and_save_crashes(days=3, product=args.product)
    paths = SocorroDownloader.get_dump_paths(days=3, product=args.product)

    model_with_corpus = Doc2vecModelWrapper.read_corpus(paths).train_model()
    algo = Doc2VecSimilarity(WMDCalculator.build_with_all_distances(model_with_corpus.model, model_with_corpus.corpus))

    print(args.one + ' vs ' + args.two)
    traces1 = StackTracesGetter.get_stack_traces_for_signature(paths, args.one)
    traces2 = StackTracesGetter.get_stack_traces_for_signature(paths, args.two)
    similarities = algo.signatures_similarity(traces1, traces2)

    print('first signature:')
    for t in traces1:
        print(t)
    print('second signature:')
    for t in traces2:
        print(t)
    print('similarities matrix:')
    pprint.pprint(similarities)
