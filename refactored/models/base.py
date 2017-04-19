from abc import abstractmethod


class Algorithm(object):
    @abstractmethod
    def read_data(self, data):
        pass

    @abstractmethod
    def train_model(self):
        """"""
        pass

    @abstractmethod
    def top_similar_traces(self, stack_trace, top_n):
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


class Word2VecBased(object):
    def __init__(self, distance_func):
        """
        :param distance_func: should take two vectors and return distance between them
        """
        self.distance_func = distance_func

    @abstractmethod
    def traces_similarity(self, stack_trace1, stack_trace2):
        """
        Calculate similarity using `distance_func` on vectors inferred from trained model

        :return: similarity. higher is more better
        """
        pass


class WithSaveLoad(object):
    @abstractmethod
    def save(self, directory):
        """Save complex object to directory. It may be stored in multiple files"""
        pass

    @staticmethod
    @abstractmethod
    def load(directory):
        """Load complex object from directory. It may be stored in multiple files"""
        pass
