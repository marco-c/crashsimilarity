# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import utils


def get_signatures_from_bug(bug_id):
    url = 'https://bugzilla.mozilla.org/rest/bug'
    response = utils.get_with_retries(url, params={'id': bug_id})
    response.raise_for_status()
    return [sig.strip(' [@]') for sig in response.json()['bugs'][0]['cf_crash_signature'].split('\r\n')]


if __name__ == "__main__":
    print(get_signatures_from_bug('1308863'))
