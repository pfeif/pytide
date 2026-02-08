from dataclasses import dataclass


@dataclass
class GetCachedMetadataResponse:
    db_id: int
    name: str
    latitude: float
    longitude: float


@dataclass
class FetchNoaaMetadataResponse:
    noaa_id: str
    name: str
    latitude: float
    longitude: float


@dataclass
class SaveMetadataRequest:
    noaa_id: str
    name: str
    latitude: float
    longitude: float
