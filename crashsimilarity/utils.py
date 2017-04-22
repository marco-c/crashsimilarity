import os
import errno
from datetime import datetime

from smart_open import smart_open
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def utc_today():
    return datetime.utcnow().date()


def get_with_retries(url, params=None, headers=None):  # can't be tested with requests_mock.Mocker() for unknown reason
    s = requests.Session()
    s.mount('https://',
            HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
    return s.get(url, params=params, headers=headers)


def read_files(file_names, open_file_function=smart_open):
    for name in file_names:
        with open_file_function(name) as f:
            for line in f:
                yield line if isinstance(line, str) else line.decode('utf8')


def create_dir(path):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
