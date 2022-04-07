import requests

from osm2geojson import json2geojson

import json
import logging

from time import sleep
from typing import Any, Dict, Optional


OVERPASS_API_URL = 'https://lz4.overpass-api.de/api/interpreter'
OVERPASS_QUERY_FILE = 'overpass_query.txt'

OVERPASS_RETRIES = 5
OVERPASS_TIMEOUT = 30  # seconds

GEOJSON_FILENAME = 'data.geojson'


def download_data() -> Optional[Dict[Any, Any]]:
    with open(OVERPASS_QUERY_FILE, 'r') as f:
        query = f.read().strip()

    logging.info(f'Read overpass query from file: {OVERPASS_QUERY_FILE}')
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

    overpass_data = download_data()
    if overpass_data is None:
        logging.info('Empty overpass data. Exiting!')
        exit(1)

    logging.info(f'Filtering data...')
    overpass_data = filter_data(overpass_data)

    logging.info(f'Parsing overpass data to geojson...')
    geojson = json2geojson(overpass_data)

    with open(GEOJSON_FILENAME, 'w') as f:
        json.dump(geojson, f)

    logging.info(f'Saved geojson to file.')


if __name__ == '__main__':
    main()
