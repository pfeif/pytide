from dataclasses import dataclass


@dataclass
class GetCachedPredictionsResponse:
    time: str
    type: str
    feet: int
    inches: float


@dataclass
class FetchNoaaPredictionsResponse:
    time: str
    type: str
    change: str
