import json
import logging
import os
from datetime import timedelta

import dateutil.parser

from crashsimilarity import utils
from crashsimilarity.downloader import Downloader

SCHEMA_VERSION = '1'


def clean_old_data():
    try:
        old_schema = read_json('crashclustering_data/schema_version')[0]
    except IOError:
        old_schema = '0'

    MAX_AGE = 30

    for root, dirs, files in os.walk('crashclustering_data'):
        for name in files:
            if 'schema_version' not in name and (old_schema != SCHEMA_VERSION or dateutil.parser.parse(
                    name[-15:-5]).date() < utils.utc_today() - timedelta(MAX_AGE)):
                os.remove(os.path.join('crashclustering_data', name))


def exists(path):
    return os.path.isfile(path)


def file_path(day, product):
    return 'crashclustering_data/' + product.lower() + '-crashes-' + str(day) + '.json'


def get_path(day, product):
    return file_path(day, product)


def read_json(path):
    data = []

    with open(path, 'r') as f:
        for line in f:
            data.append(json.loads(line))

    return data


def write_json(path, data):
    with open(path, 'w') as f:
        for elem in data:
            f.write(json.dumps(elem) + '\n')


def download_day_crashes(day, product='Firefox'):
    crashes = []

    path = file_path(day, product)

    try:
        crashes += read_json(path)
    except IOError:
        pass

    finished = False

    RESULTS_NUMBER = 1000

    while not finished:
        params = {
            'product': product,
            'date': ['>=' + str(day), '<' + str(day + timedelta(1))],
            '_columns': [
                'uuid',
                'signature',
                'proto_signature',
            ],
            '_results_number': RESULTS_NUMBER,
            '_results_offset': len(crashes),
            '_facets_size': 0,
        }

        logging.debug(str(day) + ' - ' + str(len(crashes)))

        response = Downloader.get_with_retries('https://crash-stats.mozilla.com/api/SuperSearch', params=params)
        response.raise_for_status()

        found = response.json()['hits']
        crashes += found

        if len(found) < RESULTS_NUMBER:
            finished = True

    uuids = set()
    filtered_crashes = []
    for crash in crashes:
        if crash['uuid'] not in uuids:
            uuids.add(crash['uuid'])
            filtered_crashes.append(crash)

    write_json(path, filtered_crashes)


def download_crashes(days, product='Firefox'):
    global SCHEMA_VERSION

    if not os.path.exists('crashclustering_data'):
        os.mkdir('crashclustering_data')

    clean_old_data()
    write_json('crashclustering_data/schema_version', [SCHEMA_VERSION])

    for i in range(0, days):
        download_day_crashes(utils.utc_today() - timedelta(i), product)


def get_paths(days, product='Firefox'):
    last_day = utils.utc_today()
    path = get_path(last_day, product)
    if not exists(path):
        last_day -= timedelta(1)

    return [get_path(last_day - timedelta(i), product) for i in range(0, days)]
