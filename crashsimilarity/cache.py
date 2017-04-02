import json

import utils


class Cache(object):
    def __init__(self, traces=None, downloader_cache=None):
        # TODO: construct from Dict[signature, List[(stack_trace, uuid)] ?
        self.downloader_cache = downloader_cache if downloader_cache else dict()
        self.traces = traces if traces else []

    @staticmethod
    def build(stream):
        """build from downloaded archives"""

        # TODO: is it possible to have different `signature`s for one `proto_signature` ?
        # Exclude stack traces without symbols.
        def should_skip(stack_trace):
            return any(call in stack_trace for call in ['xul.dll@', 'XUL@', 'libxul.so@'])

        traces = []
        already_selected = set()
        for line in stream:
            data = json.loads(line)
            if should_skip(data['proto_signature']):
                continue
            processed = utils.preprocess(data['proto_signature'])
            if frozenset(processed) not in already_selected:
                # TODO: named tuple?
                traces.append((processed, data['signature'], data['uuid']))
                already_selected.add(frozenset(processed))
        return Cache(traces=traces)

    def update_downloader_cache(self, key, value):
        """update `self.downloader_cache` and flush it to disk"""
        pass
