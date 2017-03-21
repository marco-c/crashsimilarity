# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import bisect
import json
import multiprocessing
import os
import random
import time
import logging
from datetime import datetime

import gensim
import numpy as np
from pyemd import emd
import pyximport

import download_data
import utils

pyximport.install()


# Checks if the model has been trained in the last 24 hours
def check_training_time():
    with open('last_trained.txt', 'r') as myfile:
        data = myfile.read()
        last_trained_time = datetime.strptime(data, '%b %d %Y %I:%M%p').day

    return datetime.today().day - last_trained_time < 1


def store_training_time():
    with open("last_trained.txt", "w") as text_file:
        text_file.write(datetime.today().strftime('%b %d %Y %I:%M%p'))


def clean_func(func):
    func = func.lower().replace('\n', '')

    if '@0x' in func:
        return func[:func.index('@0x') + 3]

    return func


def preprocess(stack_trace):
    return [clean_func(f) for f in stack_trace.split(' | ')][:10]  # XXX: 10 bottom frames or all of them?


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

        processed = preprocess(proto_signature)

        if frozenset(processed) not in already_selected:
            elems.append((processed, data['signature']))
        already_selected.add(frozenset(processed))

    return [gensim.models.doc2vec.TaggedDocument(trace, [i, signature]) for i, (trace, signature) in enumerate(elems)]


def get_stack_trace_from_crashid(crash_id):
    url = 'https://crash-stats.mozilla.com/api/ProcessedCrash'
    params = {
        'crash_id': crash_id
    }
    res = utils.get_with_retries(url, params)
    return res.json()['proto_signature']


def get_stack_traces_for_signature(fnames, signature, traces_num=100):
    traces = set()

    # query stack traces online
    url = 'https://crash-stats.mozilla.com/api/SuperSearch'
    params = {
        'signature': '=' + signature,
        '_facets': ['proto_signature'],
        '_facets_size': traces_num,
        '_results_number': 0
    }
    res = utils.get_with_retries(url, params)
    records = res.json()['facets']['proto_signature']
    for record in records:
        traces.add(record['term'])

    # query stack traces from downloaded data
    for line in utils.read_files(fnames):
        data = json.loads(line)
        if data['signature'] == signature:
            traces.add(data['proto_signature'])

    return list(traces)


def get_stack_trace_for_uuid(uuid):
    data = download_data.download_crash(uuid)
    return data['proto_signature']


def train_model(corpus):
    if os.path.exists('stack_traces_model.pickle') and \
       os.path.exists('stack_traces_model.pickle.docvecs.doctag_syn0.npy'):
        return gensim.models.Doc2Vec.load('stack_traces_model.pickle')

    random.shuffle(corpus)

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.debug('CORPUS LENGTH: ' + str(len(corpus)))
    logging.debug(corpus[0])
    try:
        workers = multiprocessing.cpu_count()
    except:
        workers = 2

    model = gensim.models.doc2vec.Doc2Vec(size=100, window=8, iter=20, workers=workers)

    model.build_vocab(corpus)

    t = time.time()
    logging.debug('Training model...')
    model.train(corpus)
    logging.debug('Model trained in ' + str(time.time() - t) + ' s.')

    model.save('stack_traces_model.pickle')

    return model

# create distance_matrix using precalculate cosine distance from rwmd
def create_distance_matrix(model, dictionary, docset, all_distances):
    distances = np.zeros((len(dictionary), len(dictionary)), dtype=np.double)
    for j, w in dictionary.items():
        if w in docset:
            distances[:all_distances.shape[1], j] = all_distances[model.wv.vocab[w].index].transpose()

    return distances


# Code moodified from https://github.com/RaRe-Technologies/gensim/blob/4f0e2ae/gensim/models/keyedvectors.py#L339
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

    all_distances = 1 - np.dot(model.syn0norm, model.syn0norm[[model.vocab[word].index for word in words_to_test_clean]].transpose())
    logging.debug(all_distances.shape)

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
    logging.debug('First part done in ' + str(time.time() - t) + ' s.')

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

    logging.debug('Query done in ' + str(time.time() - t) + ' s.')

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

            if words1 == words2 or frozenset([frozenset(words1), frozenset(words2)]) in already_processed:
                continue
            already_processed.add(frozenset([frozenset(words1), frozenset(words2)]))

            similarities.append((doc1, doc2, wmdistance(model, words1, words2, distances)))

    return sorted(similarities, key=lambda v: v[2])


if __name__ == '__main__':
    # download_data.download_crashes(days=7, product='Firefox')
    # paths = download_data.get_paths(days=7, product='Firefox')
    paths = ['crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']

    corpus = read_corpus(paths)

    model = train_model(corpus)

    logging.debug(dict([(model.index2word[i], similarity) for i, similarity in enumerate(model.similar_by_word('igdumd32.dll@0x', topn=False))])['igdumd64.dll@0x'])
