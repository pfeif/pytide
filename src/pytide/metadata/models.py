from dataclasses import dataclass


@dataclass
class GetCachedMetadataResponse:
    db_id: int
    name: str
    latitude: str
    longitude: str


@dataclass
class FetchNoaaMetadataResponse:
    noaa_id: str
    name: str
    latitude: str
    longitude: str


@dataclass
class SaveMetadataRequest:
    noaa_id: str
    name: str
    latitude: str
    longitude: str
