import logging

import utils
import bugzilla
from refactored.cache import Cache
from refactored.downloader import Downloader
from refactored.models.slow_wmdistance import SlowWMDistanceModel

logging.basicConfig(level=logging.DEBUG)

# TODO: scan specific folder
ARCHIVE_FILES = ['crashsimilarity_data/firefox-crashes-2016-11-09.json.gz',
                 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz',
                 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz',
                 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz',
                 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz',
                 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz',
                 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']


def main(bug_id):
    cache = Cache.try_load_or_build(utils.read_files(ARCHIVE_FILES))
    downloader = Downloader(cache)

    signatures = bugzilla.get_signatures_from_bug(bug_id)
    stack_traces = downloader.download_stack_traces_for_signature(signatures)

    algo = SlowWMDistanceModel()
    algo.read_data(cache)
    algo.train_model()

    # TODO: add other, unrelated signatures and traces
    # TODO: evaluate results, calc auc or f1 score
    for trace in stack_traces:
        print(algo.top_similar_traces(trace))


if __name__ == '__main__':
    main(1333486)
