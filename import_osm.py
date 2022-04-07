import requests

from osm2geojson import json2geojson

import json
import logging
import os

from time import sleep
from typing import Any, Dict, Optional


QUERY_DIR = 'queries'
RESULT_DIR = 'osm_data'

CFG_LAYERS = [
    {
        'query_filename': os.path.join(QUERY_DIR, 'indoormark.ql'),
        'result_filename': os.path.join(RESULT_DIR, 'indoormark.geojson'),
    },
    {
        'query_filename': os.path.join(QUERY_DIR, 'traffic_signals.ql'),
        'result_filename': os.path.join(RESULT_DIR, 'traffic_signals.geojson'),
    },
]

OVERPASS_API_URL = 'https://lz4.overpass-api.de/api/interpreter'

OVERPASS_RETRIES = 5
OVERPASS_TIMEOUT = 30  # seconds


def download_data(overpass_query_file: str) -> Optional[Dict[Any, Any]]:
    with open(overpass_query_file, 'r') as f:
        query = f.read().strip()

    logging.info(f'Read overpass query from file: {overpass_query_file}')
    logging.info(f'Downloading overpass data...')
    for _ in range(OVERPASS_RETRIES):
        try:
            response = requests.get(OVERPASS_API_URL, params={'data': query})
            if response.status_code != 200:
                logging.warning(
                    f'Incorrect status code: {response.status_code}'
                )
                continue

            return response.json()

        except Exception as e:
            logging.error(f'Error with downloading/parsing data: {e}')

        sleep(OVERPASS_TIMEOUT)


def filter_data(overpass_data: Dict[str, Any]) -> Dict[str, Any]:
    for element in overpass_data['elements']:
        if 'tags' not in element:
            continue

        element['tags'].pop('phone', None)
        element['tags'].pop('payment', None)

        tags = element['tags']
        for key in tags.keys():
            if key.startswith('payment:'):
                element['tags'].pop(key)

    return overpass_data


def main():
    logging.basicConfig(
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d,%H:%M:%S',
        level=logging.INFO
    )

    for layer in CFG_LAYERS:
        overpass_data = download_data(layer['query_filename'])
        if overpass_data is None:
            logging.info('Empty overpass data. Exiting!')
            exit(1)

        logging.info(f'Filtering data...')
        overpass_data = filter_data(overpass_data)

        logging.info(f'Parsing overpass data to geojson...')
        geojson = json2geojson(overpass_data)

        with open(layer['result_filename'], 'w') as f:
            json.dump(geojson, f)

        logging.info(f'Saved {layer["result_filename"]}.')


if __name__ == '__main__':
    main()
