from gensim.models.doc2vec import TaggedDocument

from crashsimilarity.models.similarity.base import Algorithm


class Doc2VecSimilarity(Algorithm):
    def __init__(self, wmd_calculator):
        """
        :type wmd_calculator: WMDCalculator
        """
        self._calculator = wmd_calculator

    def top_similar_traces(self, stack_trace, corpus, top_n=10):
        _stack_trace = stack_trace.words if isinstance(stack_trace, TaggedDocument) else stack_trace
        _corpus = [c.words if isinstance(c, TaggedDocument) else c for c in corpus]

        distances = list(enumerate([self._calculator.wmdistance(_stack_trace, c) for c in _corpus]))
        return sorted(distances, key=lambda x: x[1])[:10]
        # distances = []
        # for i, doc in enumerate(_corpus):
        #     distances.append((i, self._calculator.rwmdistance(_stack_trace, doc)))
        # distances.sort(key=lambda v: v[1])
        #
        # confirmed_distances_ids = []
        # confirmed_distances = []
        #
        # for i, (doc_pos, rwmd) in enumerate(distances):
        #     # Stop once we have 'top' confirmed distances and all the rwmd lower bounds are higher than the smallest top confirmed distance.
        #     if len(confirmed_distances) >= top_n and rwmd > confirmed_distances[top_n - 1]:
        #         break
        #
        #     wmd = self._calculator.wmdistance(_stack_trace, _corpus[doc_pos])
        #
        #     j = bisect(confirmed_distances, wmd)
        #     confirmed_distances.insert(j, wmd)
        #     confirmed_distances_ids.insert(j, doc_pos)
        #
        # similarities = zip(confirmed_distances_ids, confirmed_distances)
        #
        # return sorted(similarities, key=lambda v: v[1])[:top_n]

    def signatures_similarity(self, signature1, signature2):
        pass

    def signature_coherence(self, signature):
        pass
