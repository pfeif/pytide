from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import astronomy

from pytide.astronomy.models import LunarEvents, SolarEvents


def get_observer(latitude: float, longitude: float) -> astronomy.Observer:
    return astronomy.Observer(latitude, longitude)


def calculate_sun_times(observer: astronomy.Observer, date: datetime, time_zone_info: ZoneInfo) -> SolarEvents:
    search_time = astronomy.Time(date.astimezone(timezone.utc).isoformat())

    sunrise = astronomy.SearchRiseSet(astronomy.Body.Sun, observer, astronomy.Direction.Rise, search_time, 1)
    sunset = astronomy.SearchRiseSet(astronomy.Body.Sun, observer, astronomy.Direction.Set, search_time, 1)

    return SolarEvents(
        sunrise=_localize_time(sunrise, time_zone_info) if sunrise else None,
        sunset=_localize_time(sunset, time_zone_info) if sunset else None,
    )


def calculate_moon_data(observer: astronomy.Observer, date: datetime, time_zone_info: ZoneInfo) -> LunarEvents:
    search_time = astronomy.Time(date.astimezone(timezone.utc).isoformat())

    moonrise = astronomy.SearchRiseSet(astronomy.Body.Moon, observer, astronomy.Direction.Rise, search_time, 1)
    moonset = astronomy.SearchRiseSet(astronomy.Body.Moon, observer, astronomy.Direction.Set, search_time, 1)

    phase_angle = astronomy.MoonPhase(search_time)

    return LunarEvents(
        moonrise=_localize_time(moonrise, time_zone_info) if moonrise else None,
        moonset=_localize_time(moonset, time_zone_info) if moonset else None,
        phase_angle=phase_angle,
        phase_name=_get_phase_name(phase_angle),
    )


def _localize_time(event_time: astronomy.Time, time_zone: ZoneInfo) -> datetime:
    return event_time.Utc().replace(tzinfo=timezone.utc).astimezone(time_zone)


def _get_phase_name(angle: float) -> str:
    angle %= 360

    if angle < 2 or angle > 358:
        return 'New Moon'
    if angle < 88:
        return 'Waxing Crescent'
    if angle < 92:
        return 'First Quarter'
    if angle < 178:
        return 'Waxing Gibbous'
    if angle < 182:
        return 'Full Moon'
    if angle < 268:
        return 'Waning Gibbous'
    if angle < 272:
        return 'Last Quarter'
    return 'Waning Crescent'
