import os

import gensim
from gensim.models import doc2vec
import logging

import multiprocessing

import time

from crashsimilarity import utils
from crashsimilarity.utils import StackTraceProcessor


class Doc2vecModelWrapper(object):
    _MODELS_DIR = 'trained_models/doc2vec'

    def __init__(self, corpus, model):
        self.corpus = corpus
        self.model = model

    def save_model(self, name):
        if not self.model:
            raise ValueError('nothing to save: model is empty')
        self.model.save(Doc2vecModelWrapper._path(name))

    def train_model(self, model_params=None):
        if not self.corpus:
            raise ValueError('corpus is empty')
        logging.debug('corpus length: {}'.format(self.corpus))
        if not model_params:
            try:
                workers = multiprocessing.cpu_count()
            except:
                workers = 2
            model_params = {'size': 200, 'window': 10, 'iter': 10, 'workers': workers, 'min_count': 1}
        self.model = doc2vec.Doc2Vec(**model_params)
        self.model.build_vocab(self.corpus)
        logging.debug('vocabulary size: {}'.format(len(self.model.wv.vocab)))
        start_time = time.time()
        logging.info('Training started...')
        self.model.train(self.corpus)
        logging.info('Model trained in {} seconds'.format(time.time() - start_time))
        return self

    @staticmethod
    def read_corpus(file_names):
        traces = StackTraceProcessor.process(utils.read_files(file_names), 10)
        corpus = [doc2vec.TaggedDocument(trace, [i, signature]) for i, (trace, signature) in enumerate(traces)]
        return Doc2vecModelWrapper(corpus, None)

    @staticmethod
    def delete_old_models(current_date, path, force_train):
        raise NotImplementedError

    @staticmethod
    def _path(name):
        return '{}/{}.pickle'.format(Doc2vecModelWrapper._MODELS_DIR, name)

    @staticmethod
    def load_model(name):
        path = Doc2vecModelWrapper._path(name)
        if not os.path.exists(path):
            return None
        try:
            return gensim.models.Doc2Vec.load(path)
        except:
            return None
