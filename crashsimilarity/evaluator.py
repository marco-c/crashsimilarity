import logging
import math
import pickle
import re
import time

from crashsimilarity.downloader import BugzillaDownloader, SocorroDownloader


class BugzillaClusters(object):
    def __init__(self, from_date, to_date, signatures):
        self.from_date = from_date
        self.to_date = to_date
        self.signatures = signatures

    @staticmethod
    def download_bugs(from_date, to_date, fields=None):
        if fields is None:
            fields = ['id, cf_crash_signature']
        bugs = BugzillaDownloader().download_bugs(from_date, to_date, fields)
        signatures = []
        for bug in bugs:
            clean = BugzillaClusters._clean_signatures(bug['cf_crash_signature'])
            if len(clean) > 1:
                bug['clean'] = clean
                signatures.append(bug)
        logging.debug('Get {} bugs with multiple signatures'.format(len(signatures)))
        return BugzillaClusters(from_date, to_date, signatures)

    def download_stack_traces(self, period, verbose=False):
        stack_traces = []
        t = time.time()
        for i, sig in enumerate(self.signatures):
            if verbose and i % 20 == 0:
                logging.info('downloaded {} from {}. Spent {} seconds'.format(i, len(self.signatures), time.time() - t))
            current = [SocorroDownloader().download_stack_traces_for_signature(x, 1, period) for x in sig['clean']]
            stack_traces.append(current)
        self.stack_traces = stack_traces
        return self

    def save(self):
        pickle.dump(self, open('bugzilla_clusters_{}_{}.pickle'.format(self.from_date, self.to_date)))

    @staticmethod
    def _clean_signatures(signatures):
        signatures = [re.sub(r'\(.*\)', '', s.strip('[] ')) for s in signatures.split('\r\n')]
        signatures = [s[2:] if s.startswith('@ ') else s for s in signatures]
        signatures = [s.strip() for s in signatures]
        return list(set(signatures))


class Metrics(object):  # just a namespace
    @staticmethod
    def true_positive(labels_true, labels_pred):
        ans = set()
        for i, a in enumerate(labels_true):
            for j, b in enumerate(labels_true):
                if j <= i:
                    continue
                if a == b and labels_pred[i] == labels_pred[j] and labels_pred[i] != -1:
                    ans.add((min(i, j), max(i, j)))
        return len(ans)

    @staticmethod
    def false_positive(labels_true, labels_pred):
        ans = set()
        for i, a in enumerate(labels_true):
            for j, b in enumerate(labels_true):
                if j <= i:
                    continue
                if a == b and labels_pred[i] != labels_pred[j] and labels_pred[i] != -1:
                    ans.add((min(i, j), max(i, j)))
        return len(ans)

    @staticmethod
    def false_negative(labels_true, labels_pred):
        ans = set()
        for i, a in enumerate(labels_true):
            for j, b in enumerate(labels_true):
                if j <= i:
                    continue
                if a != b and labels_pred[i] == labels_pred[j] and labels_pred[i] != -1:
                    ans.add((min(i, j), max(i, j)))
        return len(ans)

    @staticmethod
    def precision(labels_true, labels_pred):
        return float(Metrics.true_positive(labels_true, labels_pred)) / (
            Metrics.true_positive(labels_true, labels_pred) + Metrics.false_positive(labels_true, labels_pred))

    @staticmethod
    def recall(labels_true, labels_pred):
        return float(Metrics.true_positive(labels_true, labels_pred)) / (
            Metrics.true_positive(labels_true, labels_pred) + Metrics.false_negative(labels_true, labels_pred))

    @staticmethod
    def FMI(labels_true, labels_pred):
        tp = Metrics.true_positive(labels_pred, labels_true)
        fp = Metrics.false_positive(labels_pred, labels_true)
        fn = Metrics.false_negative(labels_pred, labels_true)
        return float(tp) / math.sqrt((tp + fp) * (tp + fn))
