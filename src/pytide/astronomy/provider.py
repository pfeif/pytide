from datetime import datetime

from astronomy import Body, Direction, MoonPhase, Observer, SearchRiseSet, Time

from pytide.astronomy.models import DateTime, LunarEvents, SolarEvents


def calculate_solar_data(latitude: float, longitude: float, utc_today: datetime) -> SolarEvents:
    observer = _get_observer(latitude, longitude)
    day_start = _convert_date_to_start_of_day(utc_today)

    rise, set_ = _calculate_rise_and_set(Body.Sun, observer, day_start)

    utc_events = SolarEvents(
        DateTime.from_astro_time(rise),
        DateTime.from_astro_time(set_),
    )

    return utc_events


def calculate_lunar_data(latitude: float, longitude: float, utc_today: datetime) -> LunarEvents:
    observer = _get_observer(latitude, longitude)
    day_start = _convert_date_to_start_of_day(utc_today)

    rise, set_ = _calculate_rise_and_set(Body.Moon, observer, day_start)
    phase_angle = MoonPhase(day_start)

    utc_events = LunarEvents(
        DateTime.from_astro_time(rise),
        DateTime.from_astro_time(set_),
        phase_angle,
    )

    return utc_events


def _get_observer(latitude: float, longitude: float) -> Observer:
    return Observer(latitude, longitude)


def _convert_date_to_start_of_day(today: datetime) -> Time:
    return Time.Make(today.year, today.month, today.day, 0, 0, 0)


def _calculate_rise_and_set(body: Body, observer: Observer, astro_time: Time) -> tuple[Time | None, Time | None]:
    rise = _calculate_rise(body, observer, astro_time)
    set_ = _calculate_set(body, observer, astro_time)

    return (rise, set_)


def _calculate_direction(body: Body, observer: Observer, direction: Direction, astro_time: Time) -> Time | None:
    return SearchRiseSet(body, observer, direction, astro_time, 1)


def _calculate_rise(body: Body, observer: Observer, astro_time: Time) -> Time | None:
    return _calculate_direction(body, observer, Direction.Rise, astro_time)


def _calculate_set(body: Body, observer: Observer, astro_time: Time) -> Time | None:
    return _calculate_direction(body, observer, Direction.Set, astro_time)
