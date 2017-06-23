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
        """Evaluates the similarity between two given signatures (by evaluating the similarity between the stack
        traces that are in those signatures)

        :rtype: float
        """
        pass

    @abstractmethod
    def signature_coherence(self, signature):
        """Evaluates the similarity between the stack traces in a given signature

        :return: similarities matrix
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
        if set([tuple(i) for i in signature1]) == set([tuple(i) for i in signature2]):
            return np.inf
        means = []
        for trace in signature1:
            cur = [self.distance(trace, other) for other in signature2]
            means.append(np.mean(cur))  # TODO: not so stupid?
        mean = np.mean(means)
        return 1 / mean if mean != 0 else np.inf

    def signature_coherence(self, signature):
        coherence = np.zeros((len(signature), len(signature)))
        for i in range(len(signature)):
            for j in range(i, len(signature)):
                coherence[i, j] = coherence[j, i] = self.similarity(signature[i], signature[j])
        return coherence
