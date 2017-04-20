from crashsimilarity import crash_similarity


if __name__ == '__main__':
    # download_data.download_crashes(days=7, product=args.product)
    # paths = download_data.get_paths(days=7, product=args.product)
    paths = ['crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']

    corpus = crash_similarity.read_corpus(paths)

    model = crash_similarity.train_model(corpus)

    print('mozilla::net::NeckoParent::GetValidatedAppInfo vs mozilla::net::CrashWithReason')
    similarities = crash_similarity.signature_similarity(model, paths, 'mozilla::net::NeckoParent::GetValidatedAppInfo', 'mozilla::net::CrashWithReason')
    print('Top 10')
    for similarity in similarities[:10]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
    print('Bottom 10')
    for similarity in similarities[-10:]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))

    print('\n')

    print('mozilla::MonitorAutoLock::MonitorAutoLock vs mozilla::BaseAutoLock<T>::BaseAutoLock<T>')
    similarities = crash_similarity.signature_similarity(model, paths, 'mozilla::MonitorAutoLock::MonitorAutoLock', 'mozilla::BaseAutoLock<T>::BaseAutoLock<T>')
    print('Top 10')
    for similarity in similarities[:10]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
    print('Bottom 10')
    for similarity in similarities[-10:]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
