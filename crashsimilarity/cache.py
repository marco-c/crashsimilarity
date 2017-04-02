import json


class Cache(object):

    def __init__(self, traces=None, downloader_cache=None):
        # TODO: construct from Dict[signature, List[(stack_trace, uuid)] ?
        self.downloader_cache = downloader_cache if downloader_cache else dict()
        self.traces = traces if traces else []

    @staticmethod
    def build(stream):
        """build from downloaded archives"""
        # TODO: is it possible to have different `signature`s for one `proto_signature` ?
        def preprocess(stack_trace):
            def clean(func):
                func = func.lower().replace('\n', '')
                return func[:func.index('@0x') + 3] if '@0x' in func else func
            return [clean(f) for f in stack_trace.split(' | ')]

        # Exclude stack traces without symbols.
        def should_skip(stack_trace):
            return 'xul.dll@' in stack_trace or 'XUL@' in stack_trace or 'libxul.so@' in stack_trace

        traces = []
        already_selected = set()
        for line in stream:
            data = json.loads(line)
            if should_skip(data['proto_signature']):
                continue
            processed = preprocess(data['proto_signature'])
            if frozenset(processed) not in already_selected:
                traces.append((processed, data['signature'], data['uuid']))
                already_selected.add(frozenset(processed))
        return Cache(traces=traces)
