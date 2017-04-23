import os
import json
import errno
from datetime import datetime, timedelta

from smart_open import smart_open

from crashsimilarity.downloader import SocorroDownloader


def utc_today():
    return datetime.utcnow().date()


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


CRASHSIMILARITY_DATA_DIR = '../crashsimilarity_data'


def file_path(day, product):
    return '{}/{}-crashes-{}.json'.format(CRASHSIMILARITY_DATA_DIR, product.lower(), day)


def write_json(path, data):
    with open(path, 'w') as f:
        for elem in data:
            f.write(json.dumps(elem) + '\n')


def download_crashes(days, product='Firefox'):
    if not os.path.exists(CRASHSIMILARITY_DATA_DIR):
        create_dir(CRASHSIMILARITY_DATA_DIR)

    write_json('{}/schema_version'.format(CRASHSIMILARITY_DATA_DIR), [1])

    for i in range(0, days):
        day = utc_today() - timedelta(i)
        gen = SocorroDownloader().download_day_crashes(day, product)
        write_json(file_path(day, product), gen)


def get_paths(days, product='Firefox'):
    last_day = utc_today()
    path = file_path(last_day, product)
    if not os.path.exists(path):
        last_day -= timedelta(1)
    return [f for f in [file_path(last_day - timedelta(i), product) for i in range(0, days)] if os.path.exists(f)]
