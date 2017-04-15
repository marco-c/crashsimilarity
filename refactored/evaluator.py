import logging
import random

import utils
import bugzilla
from refactored.cache import Cache
from refactored.downloader import Downloader
from refactored.models.simple_cosine import SimpleCosineDistanceModel
from refactored.cluster.base import ThresholdClusterizer

logging.basicConfig(level=logging.INFO)

# TODO: scan specific folder
ARCHIVE_FILES = ['../crashsimilarity_data/firefox-crashes-2016-11-09.json.gz',
                 '../crashsimilarity_data/firefox-crashes-2016-11-08.json.gz',
                 '../crashsimilarity_data/firefox-crashes-2016-11-07.json.gz',
                 '../crashsimilarity_data/firefox-crashes-2016-11-06.json.gz',
                 '../crashsimilarity_data/firefox-crashes-2016-11-05.json.gz',
                 '../crashsimilarity_data/firefox-crashes-2016-11-04.json.gz',
                 '../crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']


def get_random_signatures(corpus, n=20):
    idx = [random.randint(0, len(corpus) - 1) for _ in range(n)]
    return [corpus[i].words for i in idx]


def calc_similarity_scores(model, cluster, others):
    scores = dict([(i, list()) for i in range(len(cluster))])
    for i, trace in enumerate(cluster):
        for other in others:
            scores[i].append((model.traces_similarity(trace, other), "other"))
        for j, sim in enumerate(cluster):
            if j != i:
                scores[i].append((model.traces_similarity(trace, sim), "clustered"))
        scores[i] = sorted(scores[i], reverse=True)
    return scores


def main(bug_id):
    cache = Cache.try_load_or_build(utils.read_files(ARCHIVE_FILES))
    downloader = Downloader(cache)

    signatures = set(bugzilla.get_signatures_from_bug(bug_id))
    #  get only one trace per signature for now
    stack_traces = [st[0] for st in [downloader.download_stack_traces_for_signature(s) for s in signatures] if st]

    model = SimpleCosineDistanceModel.load('../simple-cosine-model')
    if not model:
        model = SimpleCosineDistanceModel()
        model.read_data(cache.traces)
        model.train_model()
    # TODO: write function to calculate all scores
    clusterizer = ThresholdClusterizer(0.82)

    coherence = model.signature_coherence(stack_traces)
    print(coherence)
    # Verify that the tool considers those signatures to be similar
    print('all in cluster are similar: {}'.format((coherence > clusterizer.thresh_hold).all()))

    scores = calc_similarity_scores(model, stack_traces, get_random_signatures(model.corpus))
    # Verify that the tool, given a stack trace from one of the signatures,
    # would have suggested a stack trace from one of the other signatures
    for i, score in scores.items():
        count = [0, 0]
        for s in score:
            if clusterizer.are_similar(s[0]):
                count[s[1] == 'clustered'] += 1
        print(count)


if __name__ == '__main__':
    main(1333486)
