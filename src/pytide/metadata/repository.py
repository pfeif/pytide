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
                row['time_zone'],
                row['utc_offset'],
                row['observes_dst'],
            )
            if row
            else None
        )


def save_metadata(requests: list[SaveMetadataRequest]) -> None:
    command = """
        INSERT INTO station(noaa_id, name, latitude, longitude, time_zone, utc_offset, observes_dst)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(noaa_id) DO UPDATE SET
            name=excluded.name,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            time_zone=excluded.time_zone,
            utc_offset=excluded.utc_offset,
            observes_dst=excluded.observes_dst,
            last_updated=CURRENT_TIMESTAMP
    """

    data = [
        (
            request.noaa_id,
            request.name,
            request.latitude,
            request.longitude,
            request.time_zone,
            request.utc_offset,
            request.observes_dst,
        )
        for request in requests
    ]

    with get_connection() as connection:
        with connection:
            connection.executemany(command, data)
