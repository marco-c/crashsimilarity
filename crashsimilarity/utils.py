import errno
import json
import os
from datetime import datetime

from smart_open import smart_open


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


def crashes_dump_file_path(day, product, data_dir):
    return '{}/{}-crashes-{}.json'.format(data_dir, product.lower(), day)


def write_json(path, data):
    with open(path, 'w') as f:
        for elem in data:
            f.write(json.dumps(elem) + '\n')
