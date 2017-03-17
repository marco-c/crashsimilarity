# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import argparse
import time
import random
import collections
import re
import gensim
import smart_open
import json
import multiprocessing
import numpy as np
import bisect
import pyximport; pyximport.install()
from datetime import datetime

# import download_data

# Checks if the model has been trained in the last 24 hours
def checkif_model_trained_in_last_24hours():
    with open('last_trained.txt', 'r') as myfile:
        data = myfile.read()
        last_trained_time = datetime.strptime(data, '%b %d %Y %I:%M%p')
        last_trained_time_value = last_trained_time.day*86400 + last_trained_time.second

    cur_time = datetime.today()
    cur_time_value = cur_time.day*86400 + cur_time.second

    str = cur_time.strftime('%b %d %Y %I:%M%p')

    with open("last_trained.txt", "w") as text_file:

        text_file.write(str + "\n")

    time_diff = cur_time_value - last_trained_time_value

    return time_diff < 86400


def clean_func(func):
    func = func.lower().replace('\n', '')

    if '@0x' in func:
        return func[:func.index('@0x') + 3]

    return func


def preprocess(stack_trace):
    return [clean_func(f) for f in stack_trace.split(' | ')][:10] # XXX: 10 bottom frames or all of them?


 # Exclude stack traces without symbols.
def should_skip(stack_trace):
    return 'xul.dll@' in stack_trace or 'XUL@' in stack_trace or 'libxul.so@' in stack_trace


def read_corpus(fnames):
    elems = []
    already_selected = set()
    for fname in fnames:
        with smart_open.smart_open(fname, encoding='iso-8859-1') as f:
            for line in f:
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
    res = utils.get_with_retries(url,params)
    return res.json()['proto_signature']


def get_stack_traces_for_signature(fnames, signature):
    traces = set()

    for fname in fnames:
        with smart_open.smart_open(fname, encoding='iso-8859-1') as f:
            for line in f:
                data = json.loads(line)
                if data['signature'] == signature:
                    traces.add(data['proto_signature'])

    return list(traces)


def get_stack_trace_for_uuid(uuid):
    data = download_data.download_crash(uuid)
    return data['proto_signature']


 def train_model(corpus):
    if os.path.exists('stack_traces_model.pickle'):
        return gensim.models.Doc2Vec.load('stack_traces_model.pickle')

    random.shuffle(corpus)

    print('CORPUS LENGTH: ' + str(len(corpus)))
    print(corpus[0])

    try:
        workers = multiprocessing.cpu_count()
    except:
        workers = 2

    model = gensim.models.doc2vec.Doc2Vec(size=100, window=8, iter=20, workers=workers)

    model.build_vocab(corpus)

    t = time.time()
    print('Training model...')
    model.train(corpus)
    print('Model trained in ' + str(time.time() - t) + ' s.')

    model.save('stack_traces_model.pickle')

    return model


def top_similar_traces(model, corpus, stack_trace, top=10):
    model.init_sims(replace=True)

    similarities = []

    words_to_test = preprocess(stack_trace)
    words_to_test_clean = [w for w in words_to_test if w in model]

    # TODO: Test if a first sorting with the average vectors is useful.
    '''
    inferred_vector = model.infer_vector(words_to_test)
    sims = model.docvecs.most_similar([inferred_vector], topn=len(model.docvecs))
    '''

    all_distances = 1 - np.dot(model.syn0norm, model.syn0norm[[model.vocab[word].index for word in words_to_test_clean]].transpose())
    print(all_distances.shape)

    t = time.time()
    distances = []
    for doc_id in range(0, len(corpus)):
        doc_words = [model.vocab[word].index for word in corpus[doc_id].words if word in model]
        if len(doc_words) != 0:
            word_dists = all_distances[doc_words]
            rwmd = max(np.sum(np.min(word_dists, axis=0)), np.sum(np.min(word_dists, axis=1)))
        else:
            rwmd = float('inf')
        distances.append((doc_id, rwmd))

    distances.sort(key=lambda v: v[1])
    print('First part done in ' + str(time.time() - t) + ' s.')

    t = time.time()
    confirmed_distances_ids = []
    confirmed_distances = []

    for i, (doc_id, rwmd_distance) in enumerate(distances):
        # Stop once we have 'top' confirmed distances and all the rwmd lower bounds are higher than the smallest top confirmed distance.
        if len(confirmed_distances) >= top and rwmd_distance > confirmed_distances[top-1]:
            print('stopping at ' + str(i))
            print(top)
            break

        # TODO: replace this with inline code (to avoid recalculating the distances).
        wmd = model.wmdistance(words_to_test, corpus[doc_id].words)
        j = bisect.bisect(confirmed_distances, wmd)
        confirmed_distances.insert(j, wmd)
        confirmed_distances_ids.insert(j, doc_id)

    similarities = zip(confirmed_distances_ids, confirmed_distances)


    print('Query done in ' + str(time.time() - t) + ' s.')

    return sorted(similarities, key=lambda v: v[1])[:top]


def signature_similarity(model, paths, signature1, signature2):
    traces1 = get_stack_traces_for_signature(paths, signature1)
    traces2 = get_stack_traces_for_signature(paths, signature2)

    similarities = []

    already_processed = set()

    for doc1 in traces1:
        words1 = [word for word in preprocess(doc1) if word in model]

        for doc2 in traces2:
            words2 = [word for word in preprocess(doc2) if word in model]

            if words1 == words2 or frozenset([frozenset(words1), frozenset(words2)]) in already_processed:
                continue
            already_processed.add(frozenset([frozenset(words1), frozenset(words2)]))

            similarities.append((doc1, doc2, model.wmdistance(words1, words2)))

    return sorted(similarities, key=lambda v: v[2])


if __name__ == '__main__':
    # download_data.download_crashes(days=7, product='Firefox')
    # paths = download_data.get_paths(days=7, product='Firefox')
    paths = ['crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']

    corpus = read_corpus(paths)

    model = train_model(corpus)

    print(dict([(model.index2word[i], similarity) for i, similarity in enumerate(model.similar_by_word('igdumd32.dll@0x', topn=False))])['igdumd64.dll@0x'])
