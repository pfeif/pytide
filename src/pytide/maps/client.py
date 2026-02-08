import requests

from pytide.maps.models import FetchGoogleMapImageRequest


def fetch_google_map_image(request: FetchGoogleMapImageRequest) -> bytes | None:
    api_url = 'https://maps.googleapis.com/maps/api/staticmap'

    parameters = {
        'markers': f'{str(request.latitude)},{str(request.longitude)}',
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
