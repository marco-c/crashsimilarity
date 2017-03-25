# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import datetime, timedelta

from smart_open import smart_open
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def utc_today():
    return datetime.utcnow().date()


def retrain_timeout_expired(training_interval=timedelta(hours=24)):
    with open('last_trained.txt', 'r') as f:
        last_trained_time = datetime.strptime(f.read(), '%b %d %Y %H:%M')
        return last_trained_time + training_interval < datetime.now()


def save_training_time():
    with open("last_trained.txt", "w") as f:
        f.write(datetime.now().strftime('%b %d %Y %H:%M'))


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
