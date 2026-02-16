from dataclasses import dataclass


@dataclass
class GetCachedPredictionsResponse:
    time: str
    type: str
    above_mean: bool
    feet: int
    inches: float


@dataclass
class FetchNoaaPredictionsResponse:
    time: str
    type: str
    change: str
