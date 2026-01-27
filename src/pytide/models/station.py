"""
Class for station data
"""

from dataclasses import dataclass, field
from email.utils import make_msgid
from typing import Any, ClassVar

from pytide.models.image import Image
from pytide.models.tide import Tide
from pytide.repositories import maps, tides


@dataclass()
class Station:
    """
    A class that holds important NOAA tide station information like a station ID, a name, and tide
    events for the station
    """

    _metadata: ClassVar[list[dict[str, Any]]] = tides.get_all_station_metadata()
    api_key: ClassVar[str]

    id_: str
    name: str = field(default='')
    latitude: str = field(init=False)
    longitude: str = field(init=False)
    tides: list[Tide] = field(default_factory=list[Tide], init=False)
    image: Image = field(init=False, repr=False)

    def __post_init__(self):
        self.__add_metadata()
        self.__add_predictions()
        self.__add_map()

    def __str__(self) -> str:
        output = f'ID# {self.id_}: {self.name} ({self.latitude}, {self.longitude})'

        for tide in self.tides:
            output += str(tide)

        return output

    def __add_metadata(self) -> None:
        """Add station name, latitude, and longitude."""
        for station in Station._metadata:
            if self.id_ != station['id']:
                continue

            self.name = station['name']

            # Six digits of decimal precision is plenty.
            self.latitude = str(round(station['lat'], 6))
            self.longitude = str(round(station['lng'], 6))
            break

    def __add_predictions(self) -> None:
        """Add tide predictions for the station."""
        predictionary = tides.get_predictions_for_station(self.id_)

        for event in predictionary['predictions']:
            tide = Tide.from_noaa_values(event['t'], event['type'], event['v'])

            self.tides.append(tide)

    def __add_map(self) -> None:
        """Add a static map image for the station."""
        image = maps.get_map_image(self.latitude, self.longitude, Station.api_key)
        content_id = make_msgid(self.id_)

        self.image = Image(image, content_id)
