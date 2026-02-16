import sqlite3

from pytide.database.cache import get_connection
from pytide.models.tide import Tide
from pytide.predictions.models import GetCachedPredictionsResponse

CACHE_EXPIRATION = '-3 hours'


def get_cached_predictions(db_id: int, target_date: str) -> list[GetCachedPredictionsResponse]:
    query = f"""
        SELECT t.time, tt.type, t.above_mean, t.feet, t.inches
        FROM tide t
            JOIN tide_type tt ON tt.id = t.type_id
        WHERE t.station_id = ?
            AND date(t.time) = ?
            AND t.last_updated >= datetime('now', '{CACHE_EXPIRATION}')
        ORDER BY t.time ASC;
    """

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(query, (db_id, target_date))

        return [
            GetCachedPredictionsResponse(
                row['time'],
                row['type'],
                row['above_mean'],
                row['feet'],
                row['inches'],
            )
            for row in cursor.fetchall()
        ]


def save_predictions(db_id: int, tides: list[Tide]) -> None:
    insert_command = """
        INSERT INTO tide(station_id, time, type_id, above_mean, feet, inches)
        VALUES (?, ?, (SELECT id FROM tide_type WHERE type = ?), ?, ?, ?)
        ON CONFLICT(station_id, time) DO UPDATE SET
            above_mean=excluded.above_mean,
            feet=excluded.feet,
            inches=excluded.inches,
            last_updated=CURRENT_TIMESTAMP;
    """

    delete_command = """
        DELETE FROM tide
        WHERE last_updated < datetime('now', '-1 day');
    """

    data = [
        (
            db_id,
            tide.event_time.strftime('%Y-%m-%d %H:%M:%S'),
            tide.tide_type,
            tide.water_level_change.above_mean,
            tide.water_level_change.feet,
            tide.water_level_change.inches,
        )
        for tide in tides
    ]

    with get_connection() as connection:
        with connection:
            connection.executemany(insert_command, data)
            connection.execute(delete_command)
