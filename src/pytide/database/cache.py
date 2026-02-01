import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from platformdirs import user_data_dir


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    data_path = Path(user_data_dir('pytide'))
    data_path.mkdir(parents=True, exist_ok=True)
    db_file = data_path / 'cache.db'

    db_initialized = db_file.exists()

    connection = sqlite3.connect(db_file)

    try:
        connection.execute('PRAGMA foreign_keys = ON;')
        connection.execute('PRAGMA journal_mode = WAL;')
        connection.execute('PRAGMA synchronous = NORMAL;')

        if not db_initialized:
            with connection:
                _create_cache(connection)

        yield connection
    finally:
        connection.close()


def delete_cache() -> tuple[Path, bool]:
    cache_path = Path(user_data_dir('pytide')) / 'cache.db'

    if cache_path.exists():
        cache_path.unlink(missing_ok=True)
        return cache_path, True

    return cache_path, False


def _create_cache(connection: sqlite3.Connection) -> None:
    create_script = """
        CREATE TABLE IF NOT EXISTS "station" (
            "id"            INTEGER PRIMARY KEY AUTOINCREMENT,
            "noaa_id"       TEXT NOT NULL UNIQUE,
            "name"          TEXT,
            "latitude"      TEXT,
            "longitude"     TEXT,
            "last_updated"  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS "tide_type" (
            "id"            INTEGER PRIMARY KEY AUTOINCREMENT,
            "type"          TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS "tide" (
            "id"            INTEGER PRIMARY KEY AUTOINCREMENT,
            "station_id"    INTEGER NOT NULL,
            "time"          TEXT NOT NULL,
            "type_id"       INTEGER NOT NULL,
            "feet"          NUMERIC NOT NULL,
            "inches"        NUMERIC NOT NULL,
            "last_updated"  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY("station_id") REFERENCES "station"("id"),
            FOREIGN KEY("type_id") REFERENCES "tide_type"("id"),
            UNIQUE("station_id", "time")
        );

        CREATE TABLE IF NOT EXISTS "map_image" (
            "id"            INTEGER PRIMARY KEY AUTOINCREMENT,
            "station_id"    INTEGER NOT NULL UNIQUE,
            "image_bytes"   BLOB NOT NULL,
            "content_id"    TEXT NOT NULL,
            "last_updated"  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY("station_id") REFERENCES "station"("id")
        );

        CREATE INDEX IF NOT EXISTS idx_tide_station_id ON tide(station_id, time);

        CREATE INDEX IF NOT EXISTS idx_tide_time ON tide(time);
        """

    seed_script = """
        INSERT OR IGNORE INTO tide_type(id, type)
        VALUES
            (1, 'High'),
            (2, 'Low');
    """

    connection.executescript(create_script)
    connection.executescript(seed_script)
