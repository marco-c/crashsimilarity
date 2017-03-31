# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import bisect
import json
import multiprocessing
import os
import random
import time

import gensim
import numpy as np

from pyemd import emd
from abc import ABCMeta, abstractmethod

import utils
import crash_similarity


class EmbeddingAlgo(object):
    """"
    Abstract Base Class for word embedding algorithms, extended for every new algorithm
    Attributes:
        fnames: list of file names that contains crashes data.
        corpus: The pre-processed data.
        model: The trained model.
    """
    __metaclass__ = ABCMeta

    def __init__(self, path):
        self.fnames = path
        self.corpus = self.read_corpus()
        self.model = self.train_model()

    @abstractmethod
    def read_corpus(self):
        pass

    def train_model(self):
        pass

    @staticmethod
    def wmdistance(model, words1, words2, all_distances):
        # Code modified from https://github.com/RaRe-Technologies/gensim/blob/4f0e2ae/gensim/models/keyedvectors.py#L339
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

        def create_distance_matrix(model, dictionary, docset, all_distances):
            distances = np.zeros((len(dictionary), len(dictionary)), dtype=np.double)
            for j, w in dictionary.items():
                if w in docset:
                    distances[:all_distances.shape[1], j] = all_distances[model.wv.vocab[w].index].transpose()

            return distances

        distances = create_distance_matrix(model, dictionary, docset, all_distances)

        assert sum(distances) != 0
        return emd(bow1, bow2, distances)

    def signature_similarity(self, paths, signature1, signature2):
        model = self.model
        model.init_sims(replace=True)
        traces1 = crash_similarity.get_stack_traces_for_signature(paths, signature1)
        traces2 = crash_similarity.get_stack_traces_for_signature(paths, signature2)

        similarities = []
        already_processed = set()

        for doc1 in traces1:
            words1 = np.unique([word for word in crash_similarity.preprocess(doc1) if word in model]).tolist()
            distances = np.array(1.0 - np.dot(model.wv.syn0norm, model.wv.syn0norm[
                [model.wv.vocab[word].index for word in words1]].transpose()), dtype=np.double)

            for doc2 in traces2:
                words2 = [word for word in crash_similarity.preprocess(doc2) if word in model]

                if words1 == words2 or frozenset([tuple(words1), tuple(words2)]) in already_processed:
                    continue
                already_processed.add(frozenset([tuple(words1), tuple(words2)]))

                similarities.append((doc1, doc2, self.wmdistance(model, words1, words2, distances)))

        return sorted(similarities, key=lambda v: v[2])


class Word2Vec(EmbeddingAlgo):

    def read_corpus(self):
        elems = []
        already_selected = set()
        for line in utils.read_files(self.fnames):
            data = json.loads(line)
            proto_signature = data['proto_signature']

            if crash_similarity.should_skip(proto_signature):
                continue

            processed = crash_similarity.preprocess(proto_signature)

            if frozenset(processed) not in already_selected:
                # No need for signatures, as word2vec doesn't require labeling
                elems.append(processed)

        return elems

    def train_model(self):
        if os.path.exists('stack_traces_word2vec_model.pickle'):
            return gensim.models.Word2Vec.load('stack_traces_word2vec_model.pickle')
        random.shuffle(self.corpus)

        print('CORPUS LENGTH: ' + str(len(self.corpus)))
        print(self.corpus[0])

        try:
            workers = multiprocessing.cpu_count()
        except:
            workers = 2

        model = gensim.models.Word2Vec(size=100, window=8, iter=20, workers=workers)

        model.build_vocab(self.corpus)
        print("Vocab Length{}".format(len(model.wv.vocab)))

        t = time.time()
        print('Training model...')
        model.train(self.corpus)
        print('Model trained in ' + str(time.time() - t) + ' s.')

        model.save('stack_traces_word2vec_model.pickle')
        return model

    def top_similar_traces(self, stack_trace, top=10):
        model = self.model
        model.init_sims(replace=True)

        similarities = []

        words_to_test = crash_similarity.preprocess(stack_trace)
        words_to_test_clean = [w for w in np.unique(words_to_test).tolist() if w in model]

        # TODO: Test if a first sorting with the average vectors is useful.
        '''
        inferred_vector = model.infer_vector(words_to_test)
        sims = model.docvecs.most_similar([inferred_vector], topn=len(model.docvecs))
        '''

        # Cos-similarity
        all_distances = np.array(1.0 - np.dot(model.wv.syn0norm, model.wv.syn0norm[
            [model.wv.vocab[word].index for word in words_to_test_clean]].transpose()), dtype=np.double)

        # Relaxed Word Mover's Distance for selecting
        t = time.time()
        distances = []
        for doc_id in range(0, len(self.corpus)):
            doc_words = [model.wv.vocab[word].index for word in self.corpus[doc_id] if word in model]

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
            if len(confirmed_distances) >= top and rwmd_distance > confirmed_distances[top - 1]:
                print('stopping at ' + str(i))
                print(top)
                break

            # TODO: replace this with inline code (to avoid recalculating the distances).
            # wmd = model.wmdistance(words_to_test, corpus[doc_id].words)                      # uses euclidian distance

            doc_words_clean = [w for w in self.corpus[doc_id] if w in model]

            wmd = self.wmdistance(model, words_to_test_clean, doc_words_clean, all_distances)  # uses cosine distance

            j = bisect.bisect(confirmed_distances, wmd)
            confirmed_distances.insert(j, wmd)
            confirmed_distances_ids.insert(j, doc_id)

        similarities = zip(confirmed_distances_ids, confirmed_distances)
        print('Query done in ' + str(time.time() - t) + ' s.')
        return sorted(similarities, key=lambda v: v[1])[:top]


class Doc2Vec(EmbeddingAlgo):

    def read_corpus(self):
        elems = []
        already_selected = set()
        for line in utils.read_files(self.fnames):
            data = json.loads(line)
            proto_signature = data['proto_signature']

            if crash_similarity.should_skip(proto_signature):
                continue

            processed = crash_similarity.preprocess(proto_signature)

            if frozenset(processed) not in already_selected:
                elems.append((processed, data['signature']))

        return [gensim.models.doc2vec.TaggedDocument(trace, [i, signature]) for i, (trace, signature) in enumerate(elems)]

    def train_model(self):
        if os.path.exists('stack_traces_doc2vec_model.pickle') and \
                os.path.exists('stack_traces_doc2vec_model.pickle.docvecs.doctag_syn0.npy'):
            return gensim.models.Doc2Vec.load('stack_traces_doc2vec_model.pickle')
        random.shuffle(self.corpus)

        print('CORPUS LENGTH: ' + str(len(self.corpus)))
        print(self.corpus[0])

        try:
            workers = multiprocessing.cpu_count()
        except:
            workers = 2

        model = gensim.models.Doc2Vec(size=100, window=8, iter=20, workers=workers)

        model.build_vocab(self.corpus)
        print("Vocab Length{}".format(len(model.wv.vocab)))

        t = time.time()
        print('Training model...')
        model.train(self.corpus)
        print('Model trained in ' + str(time.time() - t) + ' s.')

        model.save('stack_traces_doc2vec_model.pickle')
        return model

    def top_similar_traces(self, stack_trace, top=10):
        model = self.model
        model.init_sims(replace=True)

        similarities = []

        words_to_test = crash_similarity.preprocess(stack_trace)
        words_to_test_clean = [w for w in np.unique(words_to_test).tolist() if w in model]

        # TODO: Test if a first sorting with the average vectors is useful.
        '''
        inferred_vector = model.infer_vector(words_to_test)
        sims = model.docvecs.most_similar([inferred_vector], topn=len(model.docvecs))
        '''

        # Cos-similarity
        all_distances = np.array(1.0 - np.dot(model.wv.syn0norm, model.wv.syn0norm[
            [model.wv.vocab[word].index for word in words_to_test_clean]].transpose()), dtype=np.double)

        # Relaxed Word Mover's Distance for selecting
        t = time.time()
        distances = []
        for doc_id in range(0, len(self.corpus)):
            doc_words = [model.wv.vocab[word].index for word in self.corpus[doc_id].words if word in model]

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
            if len(confirmed_distances) >= top and rwmd_distance > confirmed_distances[top - 1]:
                print('stopping at ' + str(i))
                print(top)
                break

            # TODO: replace this with inline code (to avoid recalculating the distances).
            # wmd = model.wmdistance(words_to_test, corpus[doc_id].words)                      # uses euclidian distance

            doc_words_clean = [w for w in self.corpus[doc_id].words if w in model]

            wmd = self.wmdistance(model, words_to_test_clean, doc_words_clean, all_distances)  # uses cosine distance

            j = bisect.bisect(confirmed_distances, wmd)
            confirmed_distances.insert(j, wmd)
            confirmed_distances_ids.insert(j, doc_id)

        similarities = zip(confirmed_distances_ids, confirmed_distances)
        print('Query done in ' + str(time.time() - t) + ' s.')
        return sorted(similarities, key=lambda v: v[1])[:top]
