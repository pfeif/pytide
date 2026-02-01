import sqlite3

import requests

from pytide.database.cache import get_connection
from pytide.maps.models import GetCachedMapImageResponse, FetchGoogleMapImageRequest
from pytide.models.image import Image


def fetch_google_map_image(request: FetchGoogleMapImageRequest) -> bytes | None:
    api_url = 'https://maps.googleapis.com/maps/api/staticmap'

    parameters = {
        'markers': f'{request.latitude},{request.longitude}',
        'size': '320x280',
        'scale': '1',
        'zoom': '15',
        'key': f'{request.api_key}',
    }

    try:
        response = requests.get(api_url, parameters, stream=True, timeout=10)
        response.raise_for_status()

        return response.content
    except requests.RequestException as error:
        print(f'Unable to retrieve map image for {request.latitude} and {request.longitude} -> {error}')

        return None


def get_cached_map_image(db_id: int) -> GetCachedMapImageResponse | None:
    query = """
        SELECT image_bytes, content_id
        FROM map_image
        WHERE station_id = ?
            AND last_updated >= datetime('now', '-14 days');
    """

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(query, (db_id,))
        row = cursor.fetchone()

        if row:
            return GetCachedMapImageResponse(row['image_bytes'], row['content_id'])

    return None


def save_map_image(db_id: int, image: Image) -> None:
    command = """
        INSERT INTO map_image (station_id, image_bytes, content_id)
        VALUES (?, ?, ?)
        ON CONFLICT(station_id) DO UPDATE SET
            image_bytes=excluded.image_bytes,
            content_id=excluded.content_id,
            last_updated=CURRENT_TIMESTAMP;
    """

    with get_connection() as connection:
        with connection:
            connection.execute(command, (db_id, image.image, image.content_id))
