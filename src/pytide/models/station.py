from dataclasses import dataclass, field

from pytide.astronomy.models import LunarEvents, SolarEvents
from pytide.models.image import Image
from pytide.models.tide import Tide


@dataclass()
class Station:
    noaa_id: str
    db_id: int = field(init=False, repr=False)
    name: str = field(default='')

    latitude: float = field(init=False)
    longitude: float = field(init=False)

    time_zone: str = field(init=False)
    utc_offset: int = field(init=False)
    observes_dst: bool = field(init=False)

    tides: list[Tide] = field(default_factory=list[Tide], init=False)
    map_image: Image = field(init=False, repr=False)

    sun_events: SolarEvents = field(init=False)
    moon_events: LunarEvents = field(init=False)

    def __str__(self) -> str:
        output = f'ID# {self.noaa_id}: {self.name} ({self.latitude}, {self.longitude})'

        for tide in self.tides:
            output += f'\n{str(tide)}'

        return output
