from datetime import datetime
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
