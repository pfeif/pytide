"""
Functions for retrieving tide predictions and station metadata
"""
from typing import Any

import requests
from requests.exceptions import RequestException


def get_all_station_metadata() -> list[dict[str, Any]]:
    """
    Get metadata for all tide prediction stations.

    :returns: A JSON array of stations with metadata
    :rtype: list[dict[str, Any]]
    """
    # The API used here is specifically for gathering metadata about the NOAA stations. It provides
    # us with things like the name, latitude and longitude of each station.
    #   https://api.tidesandcurrents.noaa.gov/mdapi/prod/.
    api_url = 'https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=tidepredictions'

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        return response.json()['stations']
    except RequestException as error:
        raise SystemExit(f'Unable to retrieve station metadata -> {error}') from error


def get_predictions_for_station(station_id: str) -> Any:
    """
    Query NOAA and return tide predictions for the station.

    :param str station_id: The station to retrieve predictions for

    :returns: A JSON object with a key of `predictions` and an array of predictions
    :rtype: Any
    """
    # The API used here is for gathering tide predictions for the NOAA station. It'll give us
    # the times and levels of the high / low tides.
    #   https://api.tidesandcurrents.noaa.gov/api/prod/
    api_url = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'

    parameters = {
        'station': station_id,
        'date': 'today',
        'product': 'predictions',
        'datum': 'MLLW',
        'units': 'english',
        'time_zone': 'lst_ldt',
        'format': 'json',
        'interval': 'hilo',
        'application': 'Pytide: https://github.com/pfeif/pytide'
    }

    try:
        response = requests.get(api_url, params=parameters, timeout=10)
        response.raise_for_status()

        return response.json()
    except RequestException as error:
        raise SystemExit(f'Unable to retrieve tide predictions -> {error}') from error
