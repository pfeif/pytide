import requests

from pytide.predictions.models import FetchNoaaPredictionsResponse


def fetch_noaa_predictions(station_id: str) -> list[FetchNoaaPredictionsResponse]:
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
        'application': 'Pytide: https://github.com/pfeif/pytide',
    }

    try:
        response = requests.get(api_url, params=parameters, timeout=10)
        response.raise_for_status()

        tide_events = response.json()['predictions']

        return [FetchNoaaPredictionsResponse(event['t'], event['type'], event['v']) for event in tide_events]

    except requests.RequestException as error:
        raise SystemExit(f'Unable to retrieve tide predictions -> {error}') from error
