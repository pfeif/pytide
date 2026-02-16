from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple

INCHES_PER_FOOT = 12


class Measurement(NamedTuple):
    above_mean: bool
    feet: int
    inches: float


@dataclass
class Tide:
    event_time: datetime
    tide_type: str
    water_level_change: Measurement

    def __str__(self) -> str:
        return f'{self.tide_type} tide at {self.time} ({self.height})'

    @classmethod
    def from_noaa_values(cls, time: str, type_: str, change: str) -> 'Tide':
        event_time = datetime.strptime(time, '%Y-%m-%d %H:%M')
        tide_type = 'High' if type_ == 'H' else 'Low'

        combined = float(change)
        above_mean = combined >= 0
        absolute = abs(combined)
        feet = int(absolute)
        inches = round((absolute - feet) * INCHES_PER_FOOT, 1)

        return cls(event_time, tide_type, Measurement(above_mean, feet, inches))

    @property
    def time(self) -> str:
        return self.event_time.strftime('%I:%M %p').lstrip('0')

    @property
    def height(self) -> str:
        return (
            f'{"" if self.water_level_change.above_mean else "-"}'
            f'{self.water_level_change.feet} ft '
            f'{self.water_level_change.inches} in'
        )
