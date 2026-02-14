from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from pytide.astronomy.models import DateTime, LunarEvents, SolarEvents
from pytide.models.image import Image
from pytide.models.tide import Tide


@dataclass()
class Station:
    noaa_id: str
    db_id: int = field(init=False, repr=False)
    name: str = field(default='')
    latitude: float = field(init=False)
    longitude: float = field(init=False)
    tides: list[Tide] = field(default_factory=list[Tide], init=False)
    map_image: Image = field(init=False, repr=False)
    solar_events: SolarEvents = field(init=False)
    lunar_events: LunarEvents = field(init=False)
    timezone: ZoneInfo = field(init=False)

    def __str__(self) -> str:
        output = f'ID# {self.noaa_id}: {self.name} ({self.latitude}, {self.longitude})'

        for tide in self.tides:
            output += f'\n{str(tide)}'

        return output

    def format_time(self, date_time: DateTime | None) -> str:
        if not date_time or not date_time.utc_datetime:
            return 'N/A'

        return date_time.utc_datetime.astimezone(self.timezone).strftime('%I:%M %p').lstrip('0')
