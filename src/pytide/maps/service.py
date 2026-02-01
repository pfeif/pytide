from email.utils import make_msgid

from pytide.maps.repository import (
    FetchGoogleMapImageRequest,
    get_cached_map_image,
    fetch_google_map_image,
    save_map_image,
)
from pytide.models.image import Image
from pytide.models.station import Station


def hydrate_map_image(station: Station, api_key: str) -> None:
    cached_map = get_cached_map_image(station.db_id)

    if cached_map:
        station.map_image = Image(cached_map.image, cached_map.content_id)

        return None

    google_map = fetch_google_map_image(
        FetchGoogleMapImageRequest(
            station.latitude,
            station.longitude,
            api_key,
        )
    )

    if google_map:
        content_id = make_msgid(station.noaa_id)
        station.map_image = Image(google_map, content_id)

        save_map_image(station.db_id, station.map_image)
