"""
Function for retrieving static map images
"""

from typing import Any, Union

import requests
from requests import RequestException


def get_map_image(latitude: str, longitude: str, api_key: str) -> Union[bytes, Any]:
    """Return a static map image for the given latitude and longitude."""
    # Google's Maps Static API serves our static map images.
    #   https://developers.google.com/maps/documentation/maps-static/overview
    api_url = 'https://maps.googleapis.com/maps/api/staticmap'

    parameters = {
        'markers': f'{latitude},{longitude}',
        'size': '320x280',
        'scale': '1',
        'zoom': '15',
        'key': f'{api_key}'
    }

    try:
        response = requests.get(api_url, params=parameters, stream=True, timeout=10)
        response.raise_for_status()

        return response.content
    except RequestException as error:
        print(f'Unable to retrieve map image for {latitude} and {longitude} -> {error}')

        return None
