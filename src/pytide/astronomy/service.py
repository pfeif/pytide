from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder

from pytide.astronomy.provider import calculate_moon_data, calculate_sun_times, get_observer
from pytide.models.station import Station

_tf = TimezoneFinder()


def hydrate_astrological_data(station: Station) -> None:
    time_zone = _tf.timezone_at(lng=station.longitude, lat=station.latitude)
    time_zone_info = ZoneInfo(time_zone) if time_zone else ZoneInfo(str(timezone.utc))
    today = datetime.now(time_zone_info)

    observer = get_observer(station.latitude, station.longitude)

    station.sun_events = calculate_sun_times(observer, today, time_zone_info)
    station.moon_events = calculate_moon_data(observer, today, time_zone_info)
