import multiprocessing
import os
import random
import time
import logging

import gensim
from datetime import datetime

from crashsimilarity import utils
from crashsimilarity.models.base import EmbeddingAlgo


class Doc2Vec(EmbeddingAlgo):
    def _read_corpus(self):
        return [gensim.models.doc2vec.TaggedDocument(trace, [i, signature]) for i, (trace, signature) in enumerate(self._read_traces())]

    def _extract_words_from_model(self, doc_id):
        return [w for w in self._corpus[doc_id].words if w in self._model]

    def _extract_indices_from_model(self, doc_id):
        return [self._model.wv.vocab[word].index for word in self._corpus[doc_id].words if word in self._model]

    def _train_model(self, force_train=False):
        current_date = datetime.now().strftime('%d%b%Y')
        self.delete_old_models(current_date, 'trained_models/doc2vec/', force_train)

        if os.path.exists('trained_models/doc2vec/stack_traces_' + current_date + '_model.pickle'):
            return gensim.models.Doc2Vec.load('trained_models/doc2vec/stack_traces_' + current_date + '_model.pickle')

        random.shuffle(self._corpus)

        logging.debug('CORPUS LENGTH: ' + str(len(self._corpus)))
        logging.debug(self._corpus[0])

        try:
            workers = multiprocessing.cpu_count()
        except NotImplementedError:
            workers = 2

        model = gensim.models.Doc2Vec(size=100, window=8, iter=20, workers=workers)
        model.build_vocab(self._corpus)
        logging.debug("Vocab Length{}".format(len(model.wv.vocab)))

        t = time.time()
        logging.info('Training model...')
        model.train(self._corpus)
        logging.info('Model trained in ' + str(time.time() - t) + ' s.')

        utils.create_dir('trained_models/doc2vec')
        model.save('trained_models/doc2vec/stack_traces_' + current_date + '_model.pickle')

        return model
