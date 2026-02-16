import sqlite3

from pytide.database.cache import get_connection
from pytide.metadata.models import GetCachedMetadataResponse, SaveMetadataRequest

CACHE_EXPIRATION = '-7 days'


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
        SELECT id, name, latitude, longitude
        FROM station
        WHERE noaa_id = ?
            AND last_updated >= datetime('now', '{CACHE_EXPIRATION}');
    """

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(query, (noaa_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return GetCachedMetadataResponse(
            row['id'],
            row['name'],
            row['latitude'],
            row['longitude'],
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

    data = [
        (
            request.noaa_id,
            request.name,
            request.latitude,
            request.longitude,
        )
        for request in requests
    ]

    with get_connection() as connection:
        with connection:
            connection.executemany(command, data)
