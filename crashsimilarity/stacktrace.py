import json

from crashsimilarity import downloader, utils


class StackTracesGetter(object):
    @staticmethod
    def get_stack_traces_for_signature(fnames, signature, traces_num=100):
        traces = downloader.SocorroDownloader().download_stack_traces_for_signature(signature, traces_num)

        for line in utils.read_files(fnames):
            data = json.loads(line)
            if data['signature'] == signature:
                traces.add(data['proto_signature'])

        return list(traces)

    @staticmethod
    def get_stack_trace_for_uuid(uuid):
        data = downloader.SocorroDownloader().download_crash(uuid)
        return data['proto_signature']


class StackTraceProcessor(object):
    @staticmethod
    def should_skip(stack_trace):
        """Exclude stack traces without symbols"""
        return any(call in stack_trace for call in ['xul.dll@', 'XUL@', 'libxul.so@'])

    @staticmethod
    def preprocess(stack_trace, take=None):
        def clean(func):
            func = func.lower().replace('\n', '')
            return func[:func.index('@0x') + 3] if '@0x' in func else func

        traces = [clean(f).strip() for f in stack_trace.split(' | ')]
        if take:
            traces = traces[:take]
        return traces

    @staticmethod
    def process(stream, take_top_funcs=None):
        already_selected = set()
        for line in stream:
            data = json.loads(line)
            if StackTraceProcessor.should_skip(data['proto_signature']):
                continue
            processed = StackTraceProcessor.preprocess(data['proto_signature'], take_top_funcs)
            if frozenset(processed) not in already_selected:
                # TODO: named tuple?
                already_selected.add(frozenset(processed))
                yield (processed, data['signature'].lower())
