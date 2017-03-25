# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import utils
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def get_signatures_from_bug(bug_id):
    url = 'https://bugzilla.mozilla.org/rest/bug'
    response = utils.get_with_retries(url, params={'id': bug_id})
    response.raise_for_status()
    signature = []
    for sig in response.json()['bugs'][0]['cf_crash_signature'].split('\r\n'):
        pos = sig.find('[@')
        if pos != -1:
            sig = sig[pos + 2:]
        pos2 = sig.rfind(']')
        if pos2 != -1:
            sig = sig[:pos2]
        signature.append(sig.strip())
    return signature


if __name__ == "__main__":
    logging.debug(get_signatures_from_bug('1333486'))
