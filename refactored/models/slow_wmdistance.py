from gensim.models import doc2vec
import logging
import multiprocessing
import os
import random
import time

from refactored.models.base import Algorithm


class SlowWMDistanceModel(Algorithm):
    def __init__(self) -> None:
        self.model = None
        self.corpus = []
        self.index2signature = []  # signature == document tag
        self.signature2index = []

    def read_data(self, cached_data):
        for i, (stack_trace, signature, _) in enumerate(cached_data):
            self.corpus.append(doc2vec.TaggedDocument(stack_trace, [i]))
            self.index2signature.append(signature)
            self.signature2index[signature] = i

    def train_model(self, force_retrain=False):
        if not force_retrain:  # TODO: IMPORTANT! save meta info(the whole object)
            if os.path.exists('SlowWMDistanceModel.pickle'):
                logging.info("return model from cache")  # TODO: constant name (in abstract class?)
                return doc2vec.Doc2Vec.load('SlowWMDistanceModel.pickle')
        shuffled_corpus = random.shuffle(self.corpus[:])  # shallow copy

        logging.debug('corpus length: {}'.format(len(shuffled_corpus)))
        logging.debug(shuffled_corpus[0])

        try:
            workers = multiprocessing.cpu_count()
        except:
            workers = 2

        self.model = doc2vec.Doc2Vec(size=100, window=8, iter=20, workers=workers)

        self.model.build_vocab(shuffled_corpus)
        logging.debug("vocab Length: {}".format(len(self.model.wv.vocab)))

        start_time = time.time()
        logging.info('Training model...')
        self.model.train(shuffled_corpus)
        logging.info('Model trained in {} s.'.format(time.time() - start_time))

        self.model.save('SlowWMDistanceModel.pickle')

    def signatures_similarity(self, signature1, signature2):
        pass

    def signature_coherence(self, signature):
        pass

    def top_similar_traces(self, stack_trace):
        pass
