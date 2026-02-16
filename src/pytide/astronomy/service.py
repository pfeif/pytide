from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder

from pytide.astronomy.models import LunarEvents, SolarEvents
from pytide.astronomy.provider import calculate_lunar_data, calculate_solar_data
from pytide.models.station import Station

_timezone_finder = TimezoneFinder()


def hydrate_astronomical_data(station: Station) -> None:
    local_identifier = _timezone_finder.timezone_at(lng=station.longitude, lat=station.latitude)

    if not local_identifier:
        return

    station.timezone = ZoneInfo(local_identifier)
    utc_today = datetime.now(timezone.utc)

    sun_events = calculate_solar_data(station.latitude, station.longitude, utc_today)
    moon_events = calculate_lunar_data(station.latitude, station.longitude, utc_today)

    station.solar_events = SolarEvents(sun_events.rise, sun_events.set_)
    station.lunar_events = LunarEvents(moon_events.rise, moon_events.set_, moon_events.phase_angle)
