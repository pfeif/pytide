from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NamedTuple

from astronomy import Time


@dataclass
class DateTime:
    utc_datetime: datetime | None

    def __post_init__(self):
        if not self.utc_datetime:
            return
        elif not self.utc_datetime.tzinfo:
            self.utc_datetime = self.utc_datetime.replace(tzinfo=timezone.utc)
        else:
            self.utc_datetime = self.utc_datetime.astimezone(timezone.utc)

    @classmethod
    def from_astro_time(cls, astro_time: Time | None) -> 'DateTime | None':
        if not astro_time:
            return None

        return cls(utc_datetime=astro_time.Utc())


@dataclass
class AstronomicalEvents:
    rise: DateTime | None
    set_: DateTime | None


@dataclass
class SolarEvents(AstronomicalEvents):
    pass


@dataclass
class LunarEvents(AstronomicalEvents):
    phase_angle: float

    _LUNAR_PHASES = [
        (0.0, 22.5, 'New Moon', '&#127761;'),
        (22.5, 67.5, 'Waxing Crescent', '&#127762;'),
        (67.5, 112.5, 'First Quarter', '&#127763;'),
        (112.5, 157.5, 'Waxing Gibbous', '&#127764;'),
        (157.5, 202.5, 'Full Moon', '&#127765;'),
        (202.5, 247.5, 'Waning Gibbous', '&#127766;'),
        (247.5, 292.5, 'Last Quarter', '&#127767;'),
        (292.5, 337.5, 'Waning Crescent', '&#127768;'),
        (337.5, 360.0, 'New Moon', '&#127761;'),
    ]

    class LunarPhases(NamedTuple):
        name: str
        icon: str

    @property
    def _current_phase(self) -> LunarPhases:
        angle = self.phase_angle % 360.0

        for low, high, name, icon in LunarEvents._LUNAR_PHASES:
            if low <= angle < high:
                return self.LunarPhases(name, icon)

        return LunarEvents.LunarPhases('Unknown', '')

    @property
    def phase_name(self) -> str:
        return self._current_phase.name

    @property
    def phase_image(self) -> str:
        return self._current_phase.icon
