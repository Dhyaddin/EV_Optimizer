"""Uniform result types returned by every solver."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class ChargeStop:
    node: str
    arrive_pct: float
    depart_pct: float
    added_kwh: float
    queue_min: float
    charge_min: float


@dataclass
class Result:
    algorithm: str
    feasible: bool
    path: List[str]
    stops: List[ChargeStop]
    total_time_h: float
    drive_h: float
    charge_h: float
    queue_h: float
