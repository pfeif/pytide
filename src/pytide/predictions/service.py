from datetime import datetime

from pytide.models.station import Station
from pytide.models.tide import Measurement, Tide
from pytide.predictions.client import fetch_noaa_predictions
from pytide.predictions.repository import get_cached_predictions, save_predictions


def hydrate_predictions(station: Station) -> None:
    date_str = datetime.now().strftime('%Y-%m-%d')

    cached_predictions = get_cached_predictions(station.db_id, date_str)

    if cached_predictions:
        station.tides = [
            Tide(
                datetime.strptime(prediction.time, '%Y-%m-%d %H:%M:%S'),
                prediction.type,
                Measurement(prediction.above_mean, prediction.feet, prediction.inches),
            )
            for prediction in cached_predictions
        ]

        return

    noaa_predictions = fetch_noaa_predictions(station.noaa_id)

    station.tides = [Tide.from_noaa_values(event.time, event.type, event.change) for event in noaa_predictions]

    save_predictions(station.db_id, station.tides)
