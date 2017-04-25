from crashsimilarity.downloader import SocorroDownloader
from crashsimilarity import crash_similarity
import argparse
import sys


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
    # paths = ['crashsimilarity_data/firefox-crashes-2016-11-09.json', 'crashsimilarity_data/firefox-crashes-2016-11-08.json', 'crashsimilarity_data/firefox-crashes-2016-11-07.json', 'crashsimilarity_data/firefox-crashes-2016-11-06.json', 'crashsimilarity_data/firefox-crashes-2016-11-05.json', 'crashsimilarity_data/firefox-crashes-2016-11-04.json', 'crashsimilarity_data/firefox-crashes-2016-11-03.json']

    corpus = crash_similarity.read_corpus(paths)

    model = crash_similarity.train_model(corpus)

    print(args.one + ' vs ' + args.two)
    # similarities = crash_similarity.signature_similarity(model, paths,'shutdownhang | js::GCMarker::processMarkStackTop','shutdownhang | js::GCMarker::processMarkStackTop')
    similarities = crash_similarity.signature_similarity(model, paths, args.one, args.two)
    print('Top ' + str(args.top))
    for similarity in similarities[:args.top]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
    print('Bottom ' + str(args.top))
    for similarity in similarities[-int(args.top):]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
