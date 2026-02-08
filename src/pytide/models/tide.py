from dataclasses import dataclass
from datetime import datetime
import math
from typing import NamedTuple

INCHES_PER_FOOT = 12


class Measurement(NamedTuple):
    feet: int
    inches: float


@dataclass
class Tide:
    event_time: datetime
    tide_type: str
    water_level_change: Measurement

    def __str__(self) -> str:
        return f'{self.tide_type} tide at {self.time_str} ({self.height_str})'

    @classmethod
    def from_noaa_values(cls, time: str, type: str, change: str) -> 'Tide':
        event_time = datetime.strptime(time, '%Y-%m-%d %H:%M')
        tide_type = 'High' if type == 'H' else 'Low'
        total_inches = round(float(change) * INCHES_PER_FOOT, 3)
        feet = math.trunc(total_inches / INCHES_PER_FOOT)
        inches = math.fmod(total_inches, INCHES_PER_FOOT)

        return cls(event_time, tide_type, Measurement(feet, inches))

    @property
    def time_str(self) -> str:
        return self.event_time.strftime('%I:%M %p').lstrip('0')

    @property
    def height_str(self) -> str:
        return (
            f'{"-" if self.water_level_change.feet < 0 or self.water_level_change.inches < 0 else ""}'
            f'{abs(self.water_level_change.feet)} ft '
            f'{abs(self.water_level_change.inches):.1f} in'
        )
