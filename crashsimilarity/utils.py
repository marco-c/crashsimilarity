import json
import os
import errno
from datetime import datetime

from smart_open import smart_open
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def utc_today():
    return datetime.utcnow().date()


def get_with_retries(url, params=None, headers=None):
    retries = Retry(total=16, backoff_factor=1, status_forcelist=[429])

    s = requests.Session()
    s.mount('https://crash-stats.mozilla.com', HTTPAdapter(max_retries=retries))

    return s.get(url, params=params, headers=headers)


def read_files(file_names, open_file_function=smart_open):
    for name in file_names:
        with open_file_function(name) as f:
            for line in f:
                yield line if isinstance(line, str) else line.decode('utf8')


class StackTraceProcessor(object):  # just a namespace, actually
    @staticmethod
    def _should_skip(stack_trace):
        """Exclude stack traces without symbols"""
        return any(call in stack_trace for call in ['xul.dll@', 'XUL@', 'libxul.so@'])

    @staticmethod
    def _preprocess(stack_trace, take=None):
        def clean(func):
            func = func.lower().replace('\n', '')
            return func[:func.index('@0x') + 3] if '@0x' in func else func

        traces = [clean(f).strip() for f in stack_trace.split(' | ')]
        if take:
            traces = traces[:take]
        return traces

    @staticmethod
    def process(stream):
        already_selected = set()
        for line in stream:
            data = json.loads(line)
            if StackTraceProcessor._should_skip(data['proto_signature']):
                continue
            processed = StackTraceProcessor._preprocess(data['proto_signature'])
            if frozenset(processed) not in already_selected:
                # TODO: named tuple?
                already_selected.add(frozenset(processed))
                yield (processed, data['signature'].lower(), data['uuid'])


def create_dir(path):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
