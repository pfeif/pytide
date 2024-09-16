"""
Class for station data
"""

from dataclasses import dataclass, field
from email.utils import make_msgid
from typing import Any, ClassVar

import maps
import tides


@dataclass()
class Station:
    """A class that holds important NOAA tide station information like a station ID, a name, and
    tide events for the station"""
    _metadata: ClassVar[list[dict[str, Any]]] = tides.get_all_station_metadata()
    api_key: ClassVar[str]

    id_: str
    name: str = field(default='')
    latitude: str = field(init=False)
    longitude: str = field(init=False)
    tide_events: list[str] = field(default_factory=list, init=False)
    map_image: bytes = field(init=False, repr=False)
    map_image_cid: str = field(init=False, repr=False)

    def __post_init__(self):
        self._add_metadata()
        self._add_predictions()
        self._add_map()

    def __str__(self) -> str:
        output = f'ID# {self.id_}: {self.name} ({self.latitude}, {self.longitude})'

        for tide in self.tide_events:
            output += f'\n\t{tide}'

        return output

    def _add_metadata(self) -> None:
        """Add station name, latitude, and longitude."""
        for station in Station._metadata:
            if self.id_ != station['id']:
                continue

            self.name = station['name']

            # Six digits of decimal precision is plenty.
            self.latitude = str(round(station['lat'], 6))
            self.longitude = str(round(station['lng'], 6))
            break

    def _add_predictions(self) -> None:
        """Add tide predictions for the station."""
        predictionary = tides.get_predictions_for_station(self.id_)

        for event in predictionary['predictions']:
            date_time = event['t']  # 'YYYY-MM-DD HH:MM'
            water_change = event['v']  # '1.234'
            tide_type = 'High' if event['type'] == 'H' else 'Low'  # 'L' or 'H'
            tide_string = f'{date_time} {tide_type} ({water_change}\')'

            self.tide_events.append(tide_string)

    def _add_map(self) -> None:
        """Add a static map image for the station."""
        # Maps are not embeddable in email messages, so map images must be static.
        self.map_image = maps.get_map_image(self.latitude, self.longitude, Station.api_key)

        # Set a Content-ID for use in the HTML and EmailMessage later.
        self.map_image_cid = make_msgid(self.id_)
