import multiprocessing
import os
import random
import time
import logging

import gensim
from datetime import datetime

from crashsimilarity import utils
from crashsimilarity.models.base import EmbeddingAlgo


class Word2Vec(EmbeddingAlgo):
    def _read_corpus(self):
        return [elem[0] for elem in self._read_traces()]

    def _extract_words_from_model(self, doc_id):
        return [w for w in self._corpus[doc_id] if w in self._model.wv.vocab]

    def _extract_indices_from_model(self, doc_id):
        return [self._model.wv.vocab[word].index for word in self._corpus[doc_id] if word in self._model.wv.vocab]

    def _train_model(self, force_train=False):
        current_date = datetime.now().strftime('%d%b%Y')
        self.delete_old_models(current_date, 'trained_models/word2vec/', force_train)

        if os.path.exists('trained_models/word2vec/stack_traces_' + current_date + '_model.pickle'):
            return gensim.models.Word2Vec.load(
                'trained_models/word2vec/stack_traces_' + current_date + '_model.pickle')

        random.shuffle(self._corpus)

        logging.debug('CORPUS LENGTH: ' + str(len(self._corpus)))
        logging.debug(self._corpus[0])

        try:
            workers = multiprocessing.cpu_count()
        except NotImplementedError:
            workers = 2

        model = gensim.models.Word2Vec(size=100, window=8, iter=20, workers=workers)
        model.build_vocab(self._corpus)
        logging.debug("Vocab Length{}".format(len(model.wv.vocab)))

        t = time.time()
        logging.info('Training model...')
        model.train(self._corpus, total_examples=model.corpus_count, epochs=model.epochs)
        logging.info('Model trained in ' + str(time.time() - t) + ' s.')

        utils.create_dir('trained_models/word2vec')
        model.save('trained_models/word2vec/stack_traces_' + current_date + '_model.pickle')

        return model
