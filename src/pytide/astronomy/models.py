from dataclasses import dataclass
from datetime import datetime


@dataclass
class SolarEvents:
    sunrise: datetime | None
    sunset: datetime | None

    @property
    def rise_str(self) -> str | None:
        return None if self.sunrise is None else format_datetime(self.sunrise)

    @property
    def set_str(self) -> str | None:
        return None if self.sunset is None else format_datetime(self.sunset)


@dataclass
class LunarEvents:
    moonrise: datetime | None
    moonset: datetime | None
    phase_name: str
    phase_angle: float

    @property
    def rise_str(self) -> str | None:
        return None if self.moonrise is None else format_datetime(self.moonrise)

    @property
    def set_str(self) -> str | None:
        return None if self.moonset is None else format_datetime(self.moonset)


def format_datetime(event_time: datetime) -> str:
    return event_time.strftime('%I:%M %p')
