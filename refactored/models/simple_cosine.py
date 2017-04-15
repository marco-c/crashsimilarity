import multiprocessing
import os

import logging

import pickle
from gensim.models import doc2vec
import numpy as np

import utils
from refactored.models.base import Algorithm, WithSaveLoad, Word2VecBased


class SimpleCosineDistanceModel(Algorithm, Word2VecBased, WithSaveLoad):
    def __init__(self, corpus=None, model=None):
        super().__init__(None)  # TODO: pass real function here
        self.model = model
        self.corpus = corpus if corpus else []

    def read_data(self, data):
        for i, (stack_trace, signature, _) in enumerate(data):
            self.corpus.append(doc2vec.TaggedDocument(stack_trace, [i]))

    def train_model(self):
        logging.debug('corpus length: {}'.format(len(self.corpus)))
        logging.debug(self.corpus[0])

        try:
            workers = multiprocessing.cpu_count()
        except:
            workers = 2

        self.model = doc2vec.Doc2Vec(dm=0, dbow_words=1, size=100, window=8, iter=10, workers=workers)

        self.model.build_vocab(self.corpus)
        logging.debug("vocab Length: {}".format(len(self.model.wv.vocab)))

        self.model.train(self.corpus)

    def top_similar_traces(self, stack_trace, top_n=10):
        """
        Find most similar stack traces in corpus
        :param stack_trace: raw stack trace
        :param top_n: how many results
        :return: List[Tuple[index in corpus, score]]
        """
        words = self.__filter_in_model(utils.preprocess(stack_trace))
        vector = self.model.infer_vector(words)
        return self.model.docvecs.most_similar(positive=[vector], topn=top_n)

    def traces_similarity(self, stack_trace1, stack_trace2):
        words1 = self.__filter_in_model(utils.preprocess(stack_trace1))
        words2 = self.__filter_in_model(utils.preprocess(stack_trace1))
        return self.model.docvecs.similarity_unseen_docs(self.model, words1, words2)

    def signatures_similarity(self, signature1, signature2):
        means = []
        for trace in signature1:
            words = self.__filter_in_model(utils.preprocess(trace))
            dists = []
            for other in signature2:
                other_w = self.__filter_in_model(utils.preprocess(other))
                dists.append(self.model.docvecs.similarity_unseen_docs(self.model, words, other_w))
            means.append(np.mean(dists))  # TODO: not so stupid?
        return np.mean(means)

    def signature_coherence(self, signature):
        rv = np.ndarray((len(signature), len(signature)))
        for i in range(len(signature)):  # TODO: more idiomatic?
            for j in range(len(signature)):
                rv[i, j] = self.traces_similarity(signature[i], signature[j])
        return rv

    def __filter_in_model(self, words):
        return [w for w in words if w in self.model]

    def save(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        # TODO: should I really save corpus again?
        pickle.dump(self.corpus, open('{}/corpus.pickle'.format(directory), 'wb'))
        self.model.save('{}/model.pickle'.format(directory))

    @staticmethod
    def load(directory):
        try:
            corpus = pickle.load(open('{}/corpus.pickle'.format(directory), 'rb'))
            model = doc2vec.Doc2Vec.load('{}/model.pickle'.format(directory))
            return SimpleCosineDistanceModel(corpus, model)
        except:
            return None
