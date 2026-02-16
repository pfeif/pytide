import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from platformdirs import user_cache_path


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    cache_path = _get_cache_path()
    cache_path.mkdir(parents=True, exist_ok=True)
    db_file = cache_path / 'cache.db'

    db_initialized = db_file.exists()

    connection = sqlite3.connect(db_file)

    try:
        connection.execute('PRAGMA foreign_keys = ON;')
        connection.execute('PRAGMA synchronous = NORMAL;')

        if not db_initialized:
            with connection:
                _create_cache(connection)

        yield connection
    finally:
        connection.close()


def delete_cache() -> tuple[Path, bool]:
    cache_db_path = _get_cache_path() / 'cache.db'

    path_exists = cache_db_path.exists()

    if path_exists:
        cache_db_path.unlink(missing_ok=True)

    return cache_db_path, path_exists


def _get_cache_path() -> Path:
    return user_cache_path(appname='pytide', appauthor=False)


def _create_cache(connection: sqlite3.Connection) -> None:
    create_script = """
        CREATE TABLE IF NOT EXISTS "station" (
            "id"            INTEGER PRIMARY KEY AUTOINCREMENT,
            "noaa_id"       TEXT NOT NULL UNIQUE,
            "name"          TEXT,
            "latitude"      REAL,
            "longitude"     REAL,
            "last_updated"  TEXT DEFAULT CURRENT_TIMESTAMP
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
            "above_mean"    INTEGER NOT NULL,
            "feet"          INTEGER NOT NULL,
            "inches"        REAL NOT NULL,
            "last_updated"  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY("station_id") REFERENCES "station"("id") ON DELETE CASCADE,
            FOREIGN KEY("type_id") REFERENCES "tide_type"("id"),
            UNIQUE("station_id", "time")
        );

        CREATE TABLE IF NOT EXISTS "map_image" (
            "id"            INTEGER PRIMARY KEY AUTOINCREMENT,
            "station_id"    INTEGER NOT NULL UNIQUE,
            "image_bytes"   BLOB NOT NULL,
            "content_id"    TEXT NOT NULL,
            "last_updated"  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY("station_id") REFERENCES "station"("id") ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_tide_station_id ON tide(station_id);
        CREATE INDEX IF NOT EXISTS idx_tide_type_id ON tide(type_id);
        CREATE INDEX IF NOT EXISTS idx_tide_last_updated ON tide(last_updated);
        CREATE INDEX IF NOT EXISTS idx_map_image_station_id ON map_image(station_id);
        CREATE INDEX IF NOT EXISTS idx_tide_time ON tide(time);
        """

    seed_script = """
        INSERT OR IGNORE INTO tide_type(id, type)
        VALUES
            (1, 'High'),
            (2, 'Low');
    """

    connection.execute('PRAGMA journal_mode = WAL;')
    connection.executescript(create_script)
    connection.executescript(seed_script)
