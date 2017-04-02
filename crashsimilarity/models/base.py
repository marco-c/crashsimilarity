from abc import abstractmethod


class Algorithm(object):

    @abstractmethod
    def read_data(self, cached_data):
        pass

    @abstractmethod
    def train_model(self):
        """"""
        pass

    @abstractmethod
    def top_similar_traces(self, stack_trace):
        """Given a stack trace, search similar stack traces"""
        pass

    @abstractmethod
    def signatures_similarity(self, signature1, signature2):
        """Evaluates the similarity between two given signatures (by evaluating the similarity between the stack
        traces that are in those signatures) """
        pass

    @abstractmethod
    def signature_coherence(self, signature):
        """Evaluates the similarity between the stack traces in a given signature"""
        pass
