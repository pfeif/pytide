from dataclasses import dataclass


@dataclass
class GetCachedMapImageResponse:
    image: bytes
    content_id: str


@dataclass
class FetchGoogleMapImageRequest:
    latitude: str
    longitude: str
    api_key: str
