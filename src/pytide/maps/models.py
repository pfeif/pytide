from dataclasses import dataclass


@dataclass
class GetCachedMapImageResponse:
    image: bytes
    content_id: str


@dataclass
class FetchGoogleMapImageRequest:
    latitude: float
    longitude: float
    api_key: str
