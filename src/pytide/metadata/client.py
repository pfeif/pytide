import requests

from pytide.metadata.models import FetchNoaaMetadataResponse


def fetch_noaa_metadata() -> list[FetchNoaaMetadataResponse]:
    api_url = 'https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=tidepredictions'

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        stations = response.json()['stations']

        return [
            FetchNoaaMetadataResponse(
                noaa_id=station['id'],
                name=station['name'],
                latitude=round(station['lat'], 6),
                longitude=round(station['lng'], 6),
                time_zone=station['timezone'],
                utc_offset=station['timezonecorr'],
                observes_dst=station['observedst']
            )
            for station in stations
        ]

    except requests.RequestException as error:
        raise SystemExit(f'Unable to retrieve station metadata -> {error}') from error
