from pytide.metadata.client import fetch_noaa_metadata
from pytide.metadata.models import SaveMetadataRequest
from pytide.metadata.repository import cache_is_fresh, get_cached_metadata, save_metadata
from pytide.models.station import Station


def hydrate_metadata(station: Station) -> None:
    if not cache_is_fresh():
        update_metadata_cache()

    cached_metadata = get_cached_metadata(station.noaa_id)

    if cached_metadata:
        station.db_id = cached_metadata.db_id
        if not station.name:
            station.name = cached_metadata.name
        station.latitude = cached_metadata.latitude
        station.longitude = cached_metadata.longitude
        station.time_zone = cached_metadata.time_zone
        station.utc_offset = cached_metadata.utc_offset
        station.observes_dst = cached_metadata.observes_dst
    else:
        raise ValueError(f'Metadata for station ID {station.noaa_id} could not be found.')


def update_metadata_cache() -> None:
    metadata = fetch_noaa_metadata()

    values = [
        SaveMetadataRequest(
            datum.noaa_id,
            datum.name,
            datum.latitude,
            datum.longitude,
            datum.time_zone,
            datum.utc_offset,
            datum.observes_dst,
        )
        for datum in metadata
    ]

    save_metadata(values)
