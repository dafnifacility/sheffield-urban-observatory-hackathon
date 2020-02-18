"""
Get seed data and spin up database

To improve this:

Fastest Way to Load Data Into PostgreSQL Using Python
https://hakibenita.com/fast-load-data-python-postgresql
"""

import logging
import json
import tempfile
import pathlib

import psycopg2
import requests

LOGGER = logging.getLogger(__name__)

DSN = "host=localhost dbname=cold_store_db user=postgres port=54322 password=your_password"

PARAM_FILE = 'query_params.json'

DATA_SERVER_URL = 'http://localhost:5000/data/'

TABLE = 'sensor_data'

READY_FILE = '/tmp/done'


def load_params() -> dict:
    with open(PARAM_FILE, 'r') as file:
        params = json.load(file)

    LOGGER.debug(params)
    return params


def get_data(url, params: dict) -> iter:
    """Stream data via HTTP to buffer"""

    with requests.Session() as session:
        with session.get(url, params=params, stream=True) as response:
            response.raise_for_status()

            LOGGER.info("Streaming data from %s", response.url)

            yield from response.iter_lines()


def db_insert(connection_string: str, file, table):
    """Bulk upload CSV data into table"""

    with psycopg2.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            cursor.copy_from(file, table=table)

    LOGGER.info("Uploaded into table '%s'", table)


def done():
    pathlib.Path(READY_FILE).touch()


def main():
    logging.basicConfig(level=logging.DEBUG)

    params = load_params()

    # Download data and copy to database
    with tempfile.TemporaryFile() as file:
        for line in get_data(url=DATA_SERVER_URL, params=params):
            file.write(line)

        LOGGER.info('Finished streaming to %s (%s bytes)', file, file.tell())

        db_insert(connection_string=DSN, file=file, table=TABLE)

    # Flag we're finished
    done()


if __name__ == '__main__':
    main()
