import errno
import json
import os

from datetime import datetime
from smart_open import smart_open

from crashsimilarity import downloader


def utc_today():
    return datetime.utcnow().date()


def read_files(file_names, open_file_function=smart_open):
    for name in file_names:
        with open_file_function(name) as f:
            for line in f:
                yield line if isinstance(line, str) else line.decode('utf8')


class StackTracesGetter(object):
    @staticmethod
    def get_stack_traces_for_signature(fnames, signature, traces_num=100):
        traces = downloader.SocorroDownloader().download_stack_traces_for_signature(signature, traces_num)

        for line in read_files(fnames):
            data = json.loads(line)
            if data['signature'] == signature:
                traces.add(data['proto_signature'])

        return list(traces)

    @staticmethod
    def get_stack_trace_for_uuid(uuid):
        data = downloader.SocorroDownloader().download_crash(uuid)
        return data['proto_signature']


class StackTraceProcessor(object):  # just a namespace, actually
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


def create_dir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e


def crashes_dump_file_path(day, product, data_dir):
    return '{}/{}-crashes-{}.json'.format(data_dir, product.lower(), day)


def write_json(path, data):
    with open(path, 'w') as f:
        for elem in data:
            f.write(json.dumps(elem) + '\n')
