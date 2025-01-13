import dataclasses
from enum import Enum


@dataclasses.dataclass(frozen=True)
class CanvasPoint:
    x: float
    y: float


@dataclasses.dataclass(frozen=True)
class CanvasMarker(CanvasPoint):
    marker_id: int


class CanvasScaleType(str, Enum):
    linear = "linear"
    log = "log"


@dataclasses.dataclass(frozen=True)
class CanvasAxis:
    min_: float
    max_: float
    scale: CanvasScaleType = CanvasScaleType.linear
    name: str | None = None


@dataclasses.dataclass(frozen=True)
class CanvasLegendElement:
    marker_id: int
    sequence_name: str | None


@dataclasses.dataclass(frozen=True)
class CanvasLegend:
    legend_elements: list[CanvasLegendElement]


@dataclasses.dataclass(frozen=True)
class Canvas:
    markers: list[CanvasMarker]
    x_axis: CanvasAxis
    y_axis: CanvasAxis
    legend: CanvasLegend
