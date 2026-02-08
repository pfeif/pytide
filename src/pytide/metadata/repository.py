import sqlite3

import requests

from pytide.database.cache import get_connection
from pytide.metadata.models import FetchNoaaMetadataResponse, GetCachedMetadataResponse, SaveMetadataRequest

CACHE_EXPIRATION = '-7 days'


def fetch_noaa_metadata() -> list[FetchNoaaMetadataResponse]:
    api_url = 'https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=tidepredictions'

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        stations = response.json()['stations']

        return [
            FetchNoaaMetadataResponse(
                station['id'],
                station['name'],
                round(station['lat'], 6),
                round(station['lng'], 6),
            )
            for station in stations
        ]

    except requests.RequestException as error:
        raise SystemExit(f'Unable to retrieve station metadata -> {error}') from error


def cache_is_fresh() -> bool:
    query = f"""
        SELECT EXISTS(
            SELECT 1
            FROM station
            WHERE last_updated >= datetime('now', '{CACHE_EXPIRATION}')
        );
    """

    with get_connection() as connection:
        cursor = connection.execute(query)
        return bool(cursor.fetchone()[0])


def get_cached_metadata(noaa_id: str) -> GetCachedMetadataResponse | None:
    query = f"""
        SELECT *
        FROM station
        WHERE noaa_id = ?
            AND last_updated >= datetime('now', '{CACHE_EXPIRATION}');
    """

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(query, (noaa_id,))
        row = cursor.fetchone()

        return (
            GetCachedMetadataResponse(
                row['id'],
                row['name'],
                row['latitude'],
                row['longitude'],
            )
            if row
            else None
        )


def save_metadata(requests: list[SaveMetadataRequest]) -> None:
    command = """
        INSERT INTO station(noaa_id, name, latitude, longitude)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(noaa_id) DO UPDATE SET
            name=excluded.name,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            last_updated=CURRENT_TIMESTAMP
    """

    data = [(request.noaa_id, request.name, request.latitude, request.longitude) for request in requests]

    with get_connection() as connection:
        with connection:
            connection.executemany(command, data)
