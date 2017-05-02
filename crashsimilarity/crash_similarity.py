from crashsimilarity.models import word2vec


if __name__ == '__main__':
    # download_data.download_crashes(days=7, product='Firefox')
    # paths = download_data.get_paths(days=7, product='Firefox')
    paths = ['../crashsimilarity_data/firefox-crashes-2016-11-09.json.gz'
             '../crashsimilarity_data/firefox-crashes-2016-11-08.json.gz',
             '../crashsimilarity_data/firefox-crashes-2016-11-07.json.gz',
             '../crashsimilarity_data/firefox-crashes-2016-11-06.json.gz',
             '../crashsimilarity_data/firefox-crashes-2016-11-05.json.gz',
             '../crashsimilarity_data/firefox-crashes-2016-11-04.json.gz',
             '../crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']

    model = word2vec.Word2Vec(paths, force_train=False)
    print(model.top_similar_traces("mozalloc_abort | NS_DebugBreak | nsDebugImpl::Abort | NS_InvokeByIndex | XPCWrappedNative::CallMethod | XPC_WN_CallMethod | js::InternalCallOrConstruct | InternalCall"))
    print(dict([(model.wv.index2word[i], similarity) for i, similarity in enumerate(model.wv.similar_by_word('igdumd32.dll@0x', topn=False))])['igdumd64.dll@0x'])
