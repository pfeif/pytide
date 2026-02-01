import sqlite3

import requests
from requests import RequestException

from pytide.database.cache import get_connection
from pytide.models.tide import Tide
from pytide.predictions.models import GetCachedPredictionsResponse, FetchNoaaPredictionsResponse


def fetch_noaa_predictions(station_id: str) -> list[FetchNoaaPredictionsResponse]:
    api_url = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'

    parameters = {
        'station': station_id,
        'date': 'today',
        'product': 'predictions',
        'datum': 'MLLW',
        'units': 'english',
        'time_zone': 'lst_ldt',
        'format': 'json',
        'interval': 'hilo',
        'application': 'Pytide: https://github.com/pfeif/pytide',
    }

    try:
        response = requests.get(api_url, params=parameters, timeout=10)
        response.raise_for_status()

        tide_events = response.json()['predictions']

        return [FetchNoaaPredictionsResponse(event['t'], event['type'], event['v']) for event in tide_events]

    except RequestException as error:
        raise SystemExit(f'Unable to retrieve tide predictions -> {error}') from error


def get_cached_predictions(db_id: int, target_date: str) -> list[GetCachedPredictionsResponse]:
    query = """
        SELECT t.time, tt.type, t.feet, t.inches
        FROM tide t
            JOIN tide_type tt ON tt.id = t.type_id
        WHERE t.station_id = ?
            AND date(t.time) = ?
        ORDER BY t.time ASC;
    """

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(query, (db_id, target_date))

        return [
            GetCachedPredictionsResponse(
                row['time'],
                row['type'],
                row['feet'],
                row['inches'],
            )
            for row in cursor.fetchall()
        ]


def save_predictions(db_id: int, tides: list[Tide]) -> None:
    query = """
        INSERT INTO tide(station_id, time, type_id, feet, inches)
        VALUES (?, ?, (SELECT id FROM tide_type WHERE type = ?), ?, ?)
        ON CONFLICT(station_id, time) DO NOTHING;
    """

    data = [
        (
            db_id,
            tide.event_time.strftime('%Y-%m-%d %H:%M:%S'),
            tide.tide_type,
            tide.water_level_change.feet,
            tide.water_level_change.inches,
        )
        for tide in tides
    ]

    with get_connection() as connection:
        connection.executemany(query, data)
