import numpy as np
from gensim import corpora
from gensim.models.doc2vec import TaggedDocument
from sklearn.metrics import pairwise
from pyemd import emd
import pyximport

pyximport.install()


class WMDCalculator(object):
    def __init__(self, model, w2pos, dist):
        self.model = model
        self.w2pos = w2pos
        self.dist = dist

    def rwmdistance(self, doc1, doc2):
        doc1 = [w for w in doc1 if w in self.model]
        pos1 = [self.w2pos[w] for w in doc1 if w in self.w2pos]
        doc2 = [w for w in doc2 if w in self.model]
        pos2 = [self.w2pos[w] for w in doc2 if w in self.w2pos]
        if pos1 and pos2:
            s_dists = np.zeros((len(pos2), len(pos1)), dtype=np.double)
            for i, d in enumerate(pos2):
                for j, f in enumerate(pos1):
                    s_dists[i, j] = self.dist[d][f]
            rwmd = max(np.sum(np.min(s_dists, axis=0)), np.sum(np.min(s_dists, axis=1)))
        else:
            rwmd = float('inf')
        return rwmd

    def _create_distance_matrix(self, dictionary):
        distances = np.zeros((len(dictionary), len(dictionary)), dtype=np.double)
        view = list(dictionary.items())
        for i, w1 in dictionary.items():
            for j, w2 in view[i:]:
                distances[i, j] = distances[j, i] = self.dist[int(w1), int(w2)]
        return distances

    def wmdistance(self, words1, words2):
        words1 = [w for w in words1 if w in self.model]
        words1 = [str(self.w2pos[w]) for w in words1 if w in self.w2pos]
        words2 = [w for w in words2 if w in self.model]
        words2 = [str(self.w2pos[w]) for w in words2 if w in self.w2pos]

        dictionary = corpora.Dictionary(documents=[words1, words2])
        vocab_len = len(dictionary)

        if len(words1) == 0 or len(words1) == 0:
            return np.double('inf')
        if vocab_len == 1:
            return 0.0

        def create_bow(doc):
            norm_bow = np.zeros(vocab_len, dtype=np.double)
            bow = dictionary.doc2bow(doc)
            for idx, count in bow:
                norm_bow[idx] = count / float(len(doc))
            return norm_bow

        bow1 = create_bow(words1)
        bow2 = create_bow(words2)

        distances = self._create_distance_matrix(dictionary)

        return emd(bow1, bow2, distances)

    @staticmethod
    def build_with_all_distances(model, corpus, metric='euclidean'):
        model.init_sims(replace=True)
        words = set()
        for trace in corpus:
            words.update(trace.words if isinstance(trace, TaggedDocument) else trace)

        words = [w for w in words if w in model]
        w2idx = dict([(w, i) for i, w in enumerate(words)])
        wi = [model.wv.vocab[word].index for word in words]
        wv = np.array([model.wv.syn0norm[i] for i in wi])
        dist = pairwise.pairwise_distances(wv, metric=metric)
        return WMDCalculator(model, w2idx, dist)

    @staticmethod
    def build_with_words_distances(model, corpus, words, metric='euclidean'):
        raise NotImplementedError
