import json
import os
from datetime import timedelta

from crashsimilarity import utils
from crashsimilarity.downloader import SocorroDownloader

SCHEMA_VERSION = '1'


def file_path(day, product):
    return '../crashclustering_data/' + product.lower() + '-crashes-' + str(day) + '.json'


def write_json(path, data):
    with open(path, 'w') as f:
        for elem in data:
            f.write(json.dumps(elem) + '\n')


def download_crashes(days, product='Firefox'):
    global SCHEMA_VERSION

    if not os.path.exists('../crashclustering_data'):
        os.mkdir('../crashclustering_data')

    write_json('../crashclustering_data/schema_version', [SCHEMA_VERSION])

    for i in range(0, days):
        day = utils.utc_today() - timedelta(i)
        gen = SocorroDownloader().download_day_crashes(day, product)
        write_json(file_path(day, product), gen)


def get_paths(days, product='Firefox'):
    last_day = utils.utc_today()
    path = file_path(last_day, product)
    if not os.path.exists(path):
        last_day -= timedelta(1)

    return [file_path(last_day - timedelta(i), product) for i in range(0, days)]
