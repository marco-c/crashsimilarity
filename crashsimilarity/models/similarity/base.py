from abc import abstractmethod

import numpy as np


class Algorithm(object):
    @abstractmethod
    def top_similar_traces(self, stack_trace, corpus, top_n):
        """Given a stack trace, search similar stack traces

        :return: list of (corpus index, distance(lower is better))
        :rtype: list[tuple[int, float]]
        """
        pass

    @abstractmethod
    def signatures_similarity(self, signature1, signature2):
        """Evaluates the similarity between stack traces in two given signatures

        :return: stack traces similarities matrix with shape (len(signature1), len(signature2))
        """
        pass

    @abstractmethod
    def signature_coherence(self, signature):
        """Evaluates the similarity between the stack traces in a given signature

        :return: stack traces similarities matrix with shape (len(signature), len(signature))
        """
        pass


class GenericSimilarity(Algorithm):
    def __init__(self, distance_calculator):
        """
        Similarity between stack traces is calculated as `1 / distance`

        :param distance_calculator: function that takes two stack traces and return distance between them
        """

        def similarity_calculator(a, b):
            d = distance_calculator(a, b)
            return 1 / d if d != 0 else np.inf

        self.similarity = similarity_calculator
        self.distance = distance_calculator

    def top_similar_traces(self, stack_trace, corpus, top_n):
        similarities = [(i, self.similarity(stack_trace, c)) for i, c in enumerate(corpus)]
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:top_n]

    def signatures_similarity(self, signature1, signature2):
        similarities = np.zeros((len(signature1), len(signature2)))
        for i, trace1 in enumerate(signature1):
            for j, trace2 in enumerate(signature2):
                similarities[i][j] = self.similarity(trace1, trace2)
        return similarities

    def signature_coherence(self, signature):
        return self.signatures_similarity(signature, signature)
