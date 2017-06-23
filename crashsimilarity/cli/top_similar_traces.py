# CLI INTERFACE THAT TAKES STACK TRACE AS INPUT AND RETURNS SIMILAR STACK TRACES
import pprint

from crashsimilarity.downloader import SocorroDownloader
import argparse
import sys

from crashsimilarity.models.gensim_model_wrapper import Doc2vecModelWrapper
from crashsimilarity.models.similarity.doc2vec_similarity import Doc2VecSimilarity
from crashsimilarity.models.wmd_calculator import WMDCalculator


def parse_args(args):
    parser = argparse.ArgumentParser(description='Returns the top ten similar stack traces')
    parser.add_argument('--crash_id', required=True, help='crash_id corresponding to the stack trace')
    parser.add_argument('--product', required=True, help='Product for which crash data is needed to be downloaded')
    parser.add_argument('--top', help='Number of top similar and different stack traces(Default 10)', default=10, type=int)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    SocorroDownloader.download_and_save_crashes(days=7, product=args.product)
    paths = SocorroDownloader.get_dump_paths(days=7, product=args.product)

    model_with_corpus = Doc2vecModelWrapper.read_corpus(paths).train_model()
    algo = Doc2VecSimilarity(WMDCalculator.build_with_all_distances(model_with_corpus.model, model_with_corpus.corpus))

    stack_trace = SocorroDownloader().download_crash(args.crash_id)['proto_signature']

    similarities = algo.top_similar_traces(stack_trace, model_with_corpus.corpus)

    pprint.pprint(similarities)
