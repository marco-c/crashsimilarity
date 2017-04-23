import bisect
import json
import logging
import multiprocessing
import os
import random
import time
from datetime import datetime

import gensim
import numpy as np
import pyximport
from pyemd import emd

from crashsimilarity import download_data, utils
from crashsimilarity.download_data import download_stack_traces_for_signature
from crashsimilarity.utils import preprocess

pyximport.install()


# Exclude stack traces without symbols.
def should_skip(stack_trace):
    return 'xul.dll@' in stack_trace or 'XUL@' in stack_trace or 'libxul.so@' in stack_trace


def read_corpus(fnames):
    elems = []
    already_selected = set()
    for line in utils.read_files(fnames):
        data = json.loads(line)
        proto_signature = data['proto_signature']

        if should_skip(proto_signature):
            continue

        processed = preprocess(proto_signature, 10)

        if frozenset(processed) not in already_selected:
            elems.append((processed, data['signature']))
        already_selected.add(frozenset(processed))

    return [gensim.models.doc2vec.TaggedDocument(trace, [i, signature]) for i, (trace, signature) in enumerate(elems)]


def get_stack_traces_for_signature(fnames, signature, traces_num=100):
    traces = download_stack_traces_for_signature(signature, traces_num)

    for line in utils.read_files(fnames):
        data = json.loads(line)
        if data['signature'] == signature:
            traces.add(data['proto_signature'])

    return list(traces)


def get_stack_trace_for_uuid(uuid):
    data = download_data.download_crash(uuid)
    return data['proto_signature']


def delete_old_models(current_date, force_train):
    """
    Get list of trained models inside the models directory,
    delete all models in case of user forces new training,
    if not, delete all models except of today's model
    """
    if not os.path.isdir('../models'):
        return

    if force_train:
        old_models = [model for model in os.listdir('../models')]
    else:
        old_models = [model for model in os.listdir('../models') if current_date not in model]
    for model in old_models:
        os.remove('../models/{}'.format(model))


def train_model(corpus, force_train=False):
    current_date = datetime.now().strftime('%d%b%Y')
    delete_old_models(current_date, force_train)

    if os.path.exists('../models/stack_traces_' + current_date + '_model.pickle'):
        return gensim.models.doc2vec.Doc2Vec.load('../models/stack_traces_' + current_date + '_model.pickle')

    random.shuffle(corpus)

    logging.debug('CORPUS LENGTH: ' + str(len(corpus)))
    logging.debug(corpus[0])

    try:
        workers = multiprocessing.cpu_count()
    except:
        workers = 2

    model = gensim.models.doc2vec.Doc2Vec(size=100, window=8, iter=20, workers=workers)
    model.build_vocab(corpus)
    logging.debug("Vocab Length{}".format(len(model.wv.vocab)))

    t = time.time()
    logging.info('Training model...')
    model.train(corpus)
    logging.info('Model trained in ' + str(time.time() - t) + ' s.')

    utils.create_dir('../models')
    model.save('../models/stack_traces_' + current_date + '_model.pickle')

    return model


# create distance_matrix using precalculate cosine distance from rwmd
def create_distance_matrix(model, dictionary, docset, all_distances):
    distances = np.zeros((len(dictionary), len(dictionary)), dtype=np.double)
    for j, w in dictionary.items():
        if w in docset:
            distances[:all_distances.shape[1], j] = all_distances[model.wv.vocab[w].index].transpose()

    return distances


# Code modified from https://github.com/RaRe-Technologies/gensim/blob/4f0e2ae/gensim/models/keyedvectors.py#L339
def wmdistance(model, words1, words2, all_distances):
    dictionary = gensim.corpora.Dictionary(documents=[words1, words2])
    vocab_len = len(dictionary)

    # create bag of words from document
    def create_bow(doc):
        norm_bow = np.zeros(vocab_len, dtype=np.double)
        bow = dictionary.doc2bow(doc)

        for idx, count in bow:
            norm_bow[idx] = count / float(len(doc))

        return norm_bow

    bow1 = create_bow(words1)
    bow2 = create_bow(words2)

    docset = set(words2)
    distances = create_distance_matrix(model, dictionary, docset, all_distances)

    assert sum(distances) != 0

    return emd(bow1, bow2, distances)


def top_similar_traces(model, corpus, stack_trace, top=10):
    model.init_sims(replace=True)

    similarities = []

    words_to_test = preprocess(stack_trace)
    words_to_test_clean = [w for w in np.unique(words_to_test).tolist() if w in model]

    # TODO: Test if a first sorting with the average vectors is useful.
    '''
    inferred_vector = model.infer_vector(words_to_test)
    sims = model.docvecs.most_similar([inferred_vector], topn=len(model.docvecs))
    '''

    # Cos-similarity
    all_distances = np.array(1.0 - np.dot(model.wv.syn0norm, model.wv.syn0norm[[model.wv.vocab[word].index for word in words_to_test_clean]].transpose()), dtype=np.double)

    # Relaxed Word Mover's Distance for selecting
    t = time.time()
    distances = []
    for doc_id in range(0, len(corpus)):
        doc_words = [model.wv.vocab[word].index for word in corpus[doc_id].words if word in model]
        if len(doc_words) != 0:
            word_dists = all_distances[doc_words]
            rwmd = max(np.sum(np.min(word_dists, axis=0)), np.sum(np.min(word_dists, axis=1)))
        else:
            rwmd = float('inf')
        distances.append((doc_id, rwmd))

    distances.sort(key=lambda v: v[1])
    logging.info('First part done in ' + str(time.time() - t) + ' s.')

    t = time.time()
    confirmed_distances_ids = []
    confirmed_distances = []

    for i, (doc_id, rwmd_distance) in enumerate(distances):
        # Stop once we have 'top' confirmed distances and all the rwmd lower bounds are higher than the smallest top confirmed distance.
        if len(confirmed_distances) >= top and rwmd_distance > confirmed_distances[top - 1]:
            logging.debug('stopping at ' + str(i))
            logging.debug(top)
            break

        # TODO: replace this with inline code (to avoid recalculating the distances).
        # wmd = model.wmdistance(words_to_test, corpus[doc_id].words)                      # uses euclidian distance

        doc_words_clean = [w for w in corpus[doc_id].words if w in model]
        wmd = wmdistance(model, words_to_test_clean, doc_words_clean, all_distances)  # uses cosine distance

        j = bisect.bisect(confirmed_distances, wmd)
        confirmed_distances.insert(j, wmd)
        confirmed_distances_ids.insert(j, doc_id)

    similarities = zip(confirmed_distances_ids, confirmed_distances)

    logging.info('Query done in ' + str(time.time() - t) + ' s.')

    return sorted(similarities, key=lambda v: v[1])[:top]


def signature_similarity(model, paths, signature1, signature2):
    model.init_sims(replace=True)
    traces1 = get_stack_traces_for_signature(paths, signature1)
    traces2 = get_stack_traces_for_signature(paths, signature2)

    similarities = []
    already_processed = set()

    for doc1 in traces1:
        words1 = np.unique([word for word in preprocess(doc1) if word in model]).tolist()
        distances = np.array(1.0 - np.dot(model.wv.syn0norm, model.wv.syn0norm[[model.wv.vocab[word].index for word in words1]].transpose()), dtype=np.double)

        for doc2 in traces2:
            words2 = [word for word in preprocess(doc2) if word in model]

            if words1 == words2 or frozenset([tuple(words1), tuple(words2)]) in already_processed:
                continue
            already_processed.add(frozenset([tuple(words1), tuple(words2)]))

            similarities.append((doc1, doc2, wmdistance(model, words1, words2, distances)))

    return sorted(similarities, key=lambda v: v[2])


if __name__ == '__main__':
    # download_data.download_crashes(days=7, product='Firefox')
    # paths = download_data.get_paths(days=7, product='Firefox')
    paths = ['../crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', '../crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', '../crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', '../crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', '../crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', '../crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', '../crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']
    corpus = read_corpus(paths)
    model = train_model(corpus)

    print(dict([(model.wv.index2word[i], similarity) for i, similarity in enumerate(model.wv.similar_by_word('igdumd32.dll@0x', topn=False))])['igdumd64.dll@0x'])
