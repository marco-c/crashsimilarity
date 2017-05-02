import bisect
import time
import logging

import gensim
import numpy as np
import pyximport
from pyemd import emd
from abc import ABCMeta, abstractmethod

from crashsimilarity import utils
from crashsimilarity.utils import StackTraceProcessor, StackTracesGetter

pyximport.install()


class EmbeddingAlgo(object):
    """"
    Abstract Base Class for word embedding algorithms
    Attributes:
        fnames: list of file that contains crash data
        corpus: The processed data
        model: The trained model
    """
    __metaclass__ = ABCMeta

    def __init__(self, path, force_train=False):
        """
        :param path: files that contain crash data
        :param force_train: if true: a new model is trained, if false: the current_day model is retrieved without training (if found)
        """
        self._fnames = path
        self._corpus = self._read_corpus()
        self._model = self._train_model(force_train)

    def _read_traces(self):
        return StackTraceProcessor.process(utils.read_files(self._fnames), 10)

    @abstractmethod
    def _read_corpus(self):
        pass

    @abstractmethod
    def _extract_words_from_model(self, doc_id):
        pass

    @abstractmethod
    def _extract_indices_from_model(self, doc_id):
        pass

    @abstractmethod
    def _train_model(self, force_train=False):
        pass

    def wmdistance(self, document1, document2, all_distances, distance_metric='cosine'):
        model = self._model
        if len(document1) == 0 or len(document2) == 0:
            logging.info(
                'At least one of the documents had no words that were in the vocabulary. Aborting (returning inf).')
            return float('inf')

        dictionary = gensim.corpora.Dictionary(documents=[document1, document2])
        vocab_len = len(dictionary)

        # Sets for faster look-up.
        docset1 = set(document1)
        docset2 = set(document2)

        distance_matrix = np.zeros((vocab_len, vocab_len), dtype=np.double)

        for i, t1 in dictionary.items():
            for j, t2 in dictionary.items():
                if t1 not in docset1 or t2 not in docset2:
                    continue

                if distance_metric == 'euclidean':
                    distance_matrix[i, j] = np.sqrt(np.sum((model[t1] - model[t2]) ** 2))
                elif distance_metric == 'cosine':
                    distance_matrix[i, j] = all_distances[model.wv.vocab[t2].index, i]

        if np.sum(distance_matrix) == 0.0:
            # `emd` gets stuck if the distance matrix contains only zeros.
            logging.info('The distance matrix is all zeros. Aborting (returning inf).')
            return float('inf')

        def nbow(document):
            d = np.zeros(vocab_len, dtype=np.double)
            nbow = dictionary.doc2bow(document)  # Word frequencies.
            doc_len = len(document)
            for idx, freq in nbow:
                d[idx] = freq / float(doc_len)  # Normalized word frequencies.
            return d

        # Compute nBOW representation of documents.
        d1 = nbow(document1)
        d2 = nbow(document2)

        # Compute WMD.
        return emd(d1, d2, distance_matrix)

    def top_similar_traces(self, stack_trace, top=10):
        model = self._model
        model.init_sims(replace=True)

        similarities = []

        words_to_test = StackTraceProcessor.preprocess(stack_trace)
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
        for doc_id in range(0, len(self._corpus)):
            doc_words = self._extract_indices_from_model(doc_id)
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

            doc_words_clean = self._extract_words_from_model(doc_id)
            wmd = self.wmdistance(words_to_test_clean, doc_words_clean, all_distances)

            j = bisect.bisect(confirmed_distances, wmd)
            confirmed_distances.insert(j, wmd)
            confirmed_distances_ids.insert(j, doc_id)

        similarities = zip(confirmed_distances_ids, confirmed_distances)

        logging.info('Query done in ' + str(time.time() - t) + ' s.')

        return sorted(similarities, key=lambda v: v[1])[:top]

    def signature_similarity(self, paths, signature1, signature2):
        model = self._model
        model.init_sims(replace=True)
        traces1 = StackTracesGetter.get_stack_traces_for_signature(paths, signature1)
        traces2 = StackTracesGetter.get_stack_traces_for_signature(paths, signature2)

        similarities = []
        already_processed = set()

        for doc1 in traces1:
            words1 = np.unique([word for word in StackTraceProcessor.preprocess(doc1) if word in model]).tolist()
            distances = np.array(1.0 - np.dot(model.wv.syn0norm, model.wv.syn0norm[
                [model.wv.vocab[word].index for word in words1]].transpose()), dtype=np.double)

            for doc2 in traces2:
                words2 = [word for word in StackTraceProcessor.preprocess(doc2) if word in model]

                if words1 == words2 or frozenset([tuple(words1), tuple(words2)]) in already_processed:
                    continue
                already_processed.add(frozenset([tuple(words1), tuple(words2)]))

                similarities.append((doc1, doc2, self.wmdistance(words1, words2, distances)))

        return sorted(similarities, key=lambda v: v[2])
