from dataclasses import dataclass


@dataclass
class GetCachedMetadataResponse:
    db_id: int
    name: str
    latitude: float
    longitude: float
    time_zone: str
    utc_offset: int
    observes_dst: bool


@dataclass
class FetchNoaaMetadataResponse:
    noaa_id: str
    name: str
    latitude: float
    longitude: float
    time_zone: str
    utc_offset: int
    observes_dst: bool


@dataclass
class SaveMetadataRequest:
    noaa_id: str
    name: str
    latitude: float
    longitude: float
    time_zone: str
    utc_offset: int
    observes_dst: bool
