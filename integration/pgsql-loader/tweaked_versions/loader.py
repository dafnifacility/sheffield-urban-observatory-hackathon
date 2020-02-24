"""
Get seed data and spin up database

To improve this:

Fastest Way to Load Data Into PostgreSQL Using Python
https://hakibenita.com/fast-load-data-python-postgresql
"""

import logging
import json
import tempfile
import sys
import pathlib
import time

import psycopg2, psycopg2.errors
import requests

LOGGER = logging.getLogger(__name__)

if len(sys.argv) > 1:
    PARAM_FILE = sys.argv[1]
else:
    PARAM_FILE = "/etc/uo/params.json"

# DATA_SERVER_URL = 'http://localhost:5000/data/'

TABLE = 'sensor_data'

READY_FILE = '/tmp/done'


def load_params() -> dict:
    with open(PARAM_FILE, 'r') as file:
        params = json.load(file)

    LOGGER.debug(params)
    return params


def get_data(url, params: dict) -> iter:
    """Stream data via HTTP to buffer"""
    pp = dict()
    pp["start_date"] = params["period"]["from"]
    pp["end_date"] = params["period"]["until"]
    pp["table"] = "sensor_data"

    with requests.Session() as session:
        with session.get(url, params=pp, stream=True) as response:
            response.raise_for_status()

            LOGGER.info("Streaming data from %s", response.url)

            yield from response.iter_lines()


def db_insert(connection_string: str, file, table):
    """Bulk upload CSV data into table"""

    with psycopg2.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""CREATE TABLE   sensor_data (
    timestamp TEXT default '',
    variable TEXT default '',
    units TEXT default '',
    value TEXT default '',
    location text default '',
    lat TEXT default '',
    lon TEXT default '',
    sensor_id TEXT default '',
    sensor_name TEXT default '',
    observatory TEXT default ''
)""")
            try:
                cursor.copy_from(file, table=table, columns=['timestamp','variable','units','value','location','lat','lon','sensor_id','sensor_name','observatory'])
            except psycopg2.errors.BadCopyFileFormat:
                pass
        connection.commit()

    LOGGER.info("Uploaded into table '%s'", table)


def done():
    pathlib.Path(READY_FILE).touch()


def main():
    logging.basicConfig(level=logging.DEBUG)

    params = load_params()

    # Download data and copy to database
    with open("/tmp/data", "wb") as file:
        for line in get_data(url=params["url"], params=params["params"]):
            file.write(line)

        LOGGER.info('Finished streaming to %s (%s bytes)', file, file.tell())


    with open("/tmp/data", "r") as file:
        db_insert(connection_string=params["dsn"], file=file, table=params["table"])

    # Flag we're finished
    done()
    time.sleep(999999)


if __name__ == '__main__':
    main()
