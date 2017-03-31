# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import pyximport

import download_data
import utils
import word_embeddings

pyximport.install()


def clean_func(func):
    func = func.lower().replace('\n', '')

    if '@0x' in func:
        return func[:func.index('@0x') + 3]

    return func


def preprocess(stack_trace):
    return [clean_func(f) for f in stack_trace.split(' | ')][:10]  # XXX: 10 bottom frames or all of them?


# Exclude stack traces without symbols.
def should_skip(stack_trace):
    return 'xul.dll@' in stack_trace or 'XUL@' in stack_trace or 'libxul.so@' in stack_trace


def get_stack_traces_for_signature(fnames, signature, traces_num=100):
    traces = download_data.download_stack_traces_for_signature(signature, traces_num)

    for line in utils.read_files(fnames):
        data = json.loads(line)
        if data['signature'] == signature:
            traces.add(data['proto_signature'])

    return list(traces)


def get_stack_trace_for_uuid(uuid):
    data = download_data.download_crash(uuid)
    return data['proto_signature']


if __name__ == '__main__':
    # download_data.download_crashes(days=7, product='Firefox')
    # paths = download_data.get_paths(days=7, product='Firefox')
    paths = ['crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']
    doc2vec = word_embeddings.Doc2Vec(paths)
    print doc2vec.model.similar_by_word('igdumd32.dll@0x', topn=10)