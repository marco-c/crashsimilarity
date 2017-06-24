import pprint

from crashsimilarity.downloader import SocorroDownloader
import sys
import argparse

from crashsimilarity.models.gensim_model_wrapper import Doc2vecModelWrapper
from crashsimilarity.models.similarity.doc2vec_similarity import Doc2VecSimilarity
from crashsimilarity.models.wmd_calculator import WMDCalculator
from crashsimilarity.utils import StackTracesGetter


def parse_args(args):
    parser = argparse.ArgumentParser(description='Test Signature Coherence')
    parser.add_argument('--signature', required=True, help='Signature')
    parser.add_argument('--product', required=True, help='Product for which crash data is needed to be downloaded')
    parser.add_argument('--top', help='Number of top similar and different stack traces(Default 10)', default=10, type=int)
    return parser.parse_args(args)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    SocorroDownloader.download_and_save_crashes(days=7, product=args.product)
    paths = SocorroDownloader.get_dump_paths(days=7, product=args.product)

    model_with_corpus = Doc2vecModelWrapper.read_corpus(paths).train_model()
    algo = Doc2VecSimilarity(WMDCalculator.build_with_all_distances(model_with_corpus.model, model_with_corpus.corpus))

    print(args.signature + ' \n')
    traces = StackTracesGetter.get_stack_traces_for_signature(paths, args.one)
    similarities = algo.signature_coherence(traces)

    print('signature:')
    for t in traces:
        print(t)
    print('coherence matrix:')
    pprint.pprint(similarities)
