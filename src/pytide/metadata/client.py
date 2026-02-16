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
                station['id'],
                station['name'],
                round(station['lat'], 6),
                round(station['lng'], 6),
            )
            for station in stations
        ]

    except Exception as error:
        raise SystemExit(f'Unable to retrieve station metadata -> {error}') from error
