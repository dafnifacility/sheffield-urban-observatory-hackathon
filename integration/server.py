"""
Perform a database query and export CSV data
"""

import io
import logging
import csv

import psycopg2
import flask

LOGGER = logging.getLogger(__name__)

DSN = "host=localhost dbname=cold_store_db user=postgres port=54322 password=your_password"

DEFAULT_TABLE = 'sensor_data'
DEFAULT_START_DATE = '1970-01-01'
DEFAULT_END_DATE = '9999-12-31'

APP = flask.Flask(__name__)


def get_data(query: str) -> iter:
    """
    Run query against data source and generate rows of data

    :returns: iter[dict]
    """
    with psycopg2.connect(DSN) as con:
        with con.cursor() as cur:
            cur.execute(query)

            yield from cur


def to_csv(rows: iter):
    """Emit rows of CSV data"""

    writer = None
    buffer = io.StringIO()

    for row in rows:

        LOGGER.debug(row)

        # Initialise writer
        if writer is None:
            writer = csv.DictWriter(buffer, fieldnames=row.keys())
            writer.writeheader()

        writer.writerow(row)

        yield buffer.getvalue()


def build_query() -> str:
    s = """SELECT timestamp, lat, lon, variable, unit, sensor_id, sensor_name
FROM {table}
WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'""".format(
        table=flask.request.args.get('table', DEFAULT_TABLE),
        start_date=flask.request.args.get('start_date', DEFAULT_START_DATE),
        end_date=flask.request.args.get('end_date', DEFAULT_END_DATE),
    )

    # Append predicates
    for key, value in flask.request.args.items():
        s += "\n  AND {var} IN ({val})".format(var=key, val=value)

    return s


@APP.route('/data/', methods=['GET'])
def data():
    query = build_query()

    LOGGER.debug(query)

    # Generate and stream CSV Response
    rows = get_data(query)
    return flask.Response(to_csv(rows), mimetype='text/csv')


def main():
    logging.basicConfig(level=logging.DEBUG)

    APP.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main()
