# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import crash_similarity
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    # download_data.download_crashes(days=7, product=args.product)
    # paths = download_data.get_paths(days=7, product=args.product)
    paths = ['crashsimilarity_data/firefox-crashes-2016-11-09.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-08.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-07.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-06.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-05.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-04.json.gz', 'crashsimilarity_data/firefox-crashes-2016-11-03.json.gz']

    corpus = crash_similarity.read_corpus(paths)

    model = crash_similarity.train_model(corpus)

    logging.debug('Document: <{}>\n'.format(' | '.join([u'dispatchtotracer<t>', u'jsscript::tracechildren', u'js::gcmarker::processmarkstacktop', u'js::gcmarker::drainmarkstack', u'js::gc::gcruntime::drainmarkstack', u'js::gc::gcruntime::gccycle', u'js::gc::gcruntime::collect', u'js::gc::gcruntime::gcslice', u'nsxpconnect::notifydidpaint', u'mozilla::refreshdrivertimer::tickrefreshdrivers', u'mozilla::basetimeduration<t>::frommilliseconds', u'mozilla::refreshdrivertimer::tick', u'mozilla::basetimeduration<t>::frommilliseconds', u'mozilla::vsyncrefreshdrivertimer::runrefreshdrivers', u'mozilla::basetimeduration<t>::frommilliseconds', u'mozilla::telemetry::accumulate', u'mozilla::basetimeduration<t>::frommilliseconds', u'nsrunnablemethodimpl<t>::run', u'mozilla::basetimeduration<t>::frommilliseconds', u'mozilla::ipc::messagepump::run', u'messageloop::runhandler', u'nsthreadmanager::getcurrentthread', u'nsbaseappshell::run', u'nsappstartup::run', u'xremain::xre_mainrun', u'xremain::xre_main', u'xre_main', u'_cisqrt'])))
    similarities = crash_similarity.top_similar_traces(model, corpus, ' | '.join([u'dispatchtotracer<t>', u'jsscript::tracechildren', u'js::gcmarker::processmarkstacktop', u'js::gcmarker::drainmarkstack', u'js::gc::gcruntime::drainmarkstack', u'js::gc::gcruntime::gccycle', u'js::gc::gcruntime::collect', u'js::gc::gcruntime::gcslice', u'nsxpconnect::notifydidpaint', u'mozilla::refreshdrivertimer::tickrefreshdrivers', u'mozilla::basetimeduration<t>::frommilliseconds', u'mozilla::refreshdrivertimer::tick', u'mozilla::basetimeduration<t>::frommilliseconds', u'mozilla::vsyncrefreshdrivertimer::runrefreshdrivers', u'mozilla::basetimeduration<t>::frommilliseconds', u'mozilla::telemetry::accumulate', u'mozilla::basetimeduration<t>::frommilliseconds', u'nsrunnablemethodimpl<t>::run', u'mozilla::basetimeduration<t>::frommilliseconds', u'mozilla::ipc::messagepump::run', u'messageloop::runhandler', u'nsthreadmanager::getcurrentthread', u'nsbaseappshell::run', u'nsappstartup::run', u'xremain::xre_mainrun', u'xremain::xre_main', u'xre_main', u'_cisqrt']), 20)
    for similarity in similarities:
        logging.debug(u'%s: <%s>\n' % ((corpus[similarity[0]].tags[1], similarity[1]), ' '.join(corpus[similarity[0]].words)))

    logging.debug('\n')

    logging.debug('Document: <{}>\n'.format('@0x | js::jit::computegetpropresult | js::typescript::monitor | @0x'))
    similarities = crash_similarity.top_similar_traces(model, corpus, '@0x | js::jit::computegetpropresult | js::typescript::monitor | @0x', 20)
    for similarity in similarities:
        logging.debug(u'%s: <%s>\n' % ((corpus[similarity[0]].tags[1], similarity[1]), ' '.join(corpus[similarity[0]].words)))

    logging.debug('\n')

    logging.debug('Document: <{}>\n'.format(' | '.join('extent_ad_comp extent_tree_ad_remove huge_dalloc finalizetypedarenas<t> finalizearenas js::gc::arenalists::backgroundfinalize js::gc::gcruntime::sweepbackgroundthings js::gchelperstate::dosweep js::gchelperstate::work js::helperthread::threadloop tlssetvalue js::helperthread::threadmain _pr_nativerunthread pr_root _callthreadstartex msvcr120.dll@0x basethreadinitthunk ntdll.dll@0x ntdll.dll@0x'.split(' '))))
    similarities = crash_similarity.top_similar_traces(model, corpus, ' | '.join('extent_ad_comp extent_tree_ad_remove huge_dalloc finalizetypedarenas<t> finalizearenas js::gc::arenalists::backgroundfinalize js::gc::gcruntime::sweepbackgroundthings js::gchelperstate::dosweep js::gchelperstate::work js::helperthread::threadloop tlssetvalue js::helperthread::threadmain _pr_nativerunthread pr_root _callthreadstartex msvcr120.dll@0x basethreadinitthunk ntdll.dll@0x ntdll.dll@0x'.split(' ')), 20)
    for similarity in similarities:
        logging.debug(u'%s: <%s>\n' % ((corpus[similarity[0]].tags[1], similarity[1]), ' '.join(corpus[similarity[0]].words)))

    logging.debug('\n')

    logging.debug('Document: <{}>\n'.format('mozilla::dom::indexedDB::PBackgroundIndexedDBUtilsChild::DestroySubtree | mozilla::layers::PImageBridgeChild::DestroySubtree | mozilla::layers::PImageBridgeChild::OnChannelClose | mozilla::layers::ImageBridgeShutdownStep2 | RunnableFunction<T>::Run | MessageLoop::RunTask | MessageLoop::DeferOrRunPendingTask | MessageLoop::DoWork'))
    similarities = crash_similarity.top_similar_traces(model, corpus, 'mozilla::dom::indexedDB::PBackgroundIndexedDBUtilsChild::DestroySubtree | mozilla::layers::PImageBridgeChild::DestroySubtree | mozilla::layers::PImageBridgeChild::OnChannelClose | mozilla::layers::ImageBridgeShutdownStep2 | RunnableFunction<T>::Run | MessageLoop::RunTask | MessageLoop::DeferOrRunPendingTask | MessageLoop::DoWork', 20)
    for similarity in similarities:
        logging.debug(u'%s: <%s>\n' % ((corpus[similarity[0]].tags[1], similarity[1]), ' '.join(corpus[similarity[0]].words)))
