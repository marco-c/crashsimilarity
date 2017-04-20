# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import crash_similarity


if __name__ == '__main__':
    # download_data.download_crashes(days=7, product=args.product)
    # paths = download_data.get_paths(days=7, product=args.product)
    paths = ['crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']

    corpus = crash_similarity.read_corpus(paths)

    model = crash_similarity.train_model(corpus)

    print('mozilla::net::CrashWithReason vs itself')
    similarities = crash_similarity.signature_similarity(model, paths, 'mozilla::net::CrashWithReason', 'mozilla::net::CrashWithReason')
    print('Top 10')
    for similarity in similarities[:10]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
    print('Bottom 10')
    for similarity in similarities[-10:]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))

    print('\n')

    print('mozilla::MonitorAutoLock::MonitorAutoLock vs itself')
    similarities = crash_similarity.signature_similarity(model, paths, 'mozilla::MonitorAutoLock::MonitorAutoLock', 'mozilla::MonitorAutoLock::MonitorAutoLock')
    print('Top 10')
    for similarity in similarities[:10]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
    print('Bottom 10')
    for similarity in similarities[-10:]:
        print(u'%s\n%s\n%s\n' % (similarity[2], similarity[0], similarity[1]))
