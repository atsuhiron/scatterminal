from typing import Type
import abc
import dataclasses
from enum import Enum
import math
import warnings

import canvas_layer_model as canvas


def log(value: float | int) -> float:
    return math.log10(value)


class CanvasConvertible(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_canvas(self, canvas_type: Type[canvas.TerminalConvertible]) -> canvas.TerminalConvertible:
        pass


@dataclasses.dataclass(frozen=True)
class DataSequence:
    x: list[int | float]
    y: list[int | float]
    seq_id: int
    name: str | None = None

    def __post_init__(self):
        if len(self.x) != len(self.y):
            raise ValueError("length of x and y must be equal: (index={0}, len(x)={1}, len(y)={2})".format(self.seq_id, len(self.x), len(self.y)))
        if not all(map(lambda x: isinstance(x, (int, float)), self.x)):
            raise ValueError("x must be list[int | float]: index={0}".format(self.seq_id))
        if not all(map(lambda y: isinstance(y, (int, float)), self.y)):
            raise ValueError("y must be list[int | float: index={0}".format(self.seq_id))
        if (self.name is not None) and (not self.name.isascii()):
            raise ValueError("Sequence name must be ascii: index={0}".format(self.seq_id))


class DataScaleType(str, Enum):
    linear = "linear"
    log = "log"


@dataclasses.dataclass(frozen=True)
class DataAxis:
    scale: DataScaleType = DataScaleType.linear
    name: str | None = None
    min_: int | float | None = None
    max_: int | float | None = None

    def __post_init__(self):
        if (self.name is not None) and (not self.name.isascii()):
            raise ValueError("Axis name must be ascii")
        if (self.min_ is None) != (self.max_ is None):
            raise ValueError("Axis min and Axis max should be defined simultaneously")


@dataclasses.dataclass(frozen=True)
class Data(CanvasConvertible):
    data: list[DataSequence]
    x_axis: DataAxis
    y_axis: DataAxis

    def __post_init__(self):
        if self.x_axis.scale == DataScaleType.log:
            for datum in self.data:
                if min(datum.x) <= 0:
                    warnings.warn("Non-positive value is detected on log-scale. This data point is not plotted.")
        if self.y_axis.scale == DataScaleType.log:
            for datum in self.data:
                if min(datum.y) <= 0:
                    warnings.warn("Non-positive value is detected on log-scale. This data point is not plotted.")

    def to_canvas(self, canvas_type: Type[canvas.TerminalConvertible]) -> canvas.TerminalConvertible:
        if self.x_axis.min_ is None:
            x_min = min(min(datum.x) for datum in self.data)
        else:
            x_min = self.x_axis.min_
        if self.x_axis.max_ is None:
            x_max = max(max(datum.x) for datum in self.data)
        else:
            x_max = self.x_axis.max_
        if self.x_axis.scale == DataScaleType.linear:
            x_min = math.log10(x_min)
            x_max = math.log10(x_max)

        if self.y_axis.min_ is None:
            y_min = min(min(datum.y) for datum in self.data)
        else:
            y_min = self.y_axis.min_
        if self.y_axis.max_ is None:
            y_max = max(max(datum.y) for datum in self.data)
        else:
            y_max = self.y_axis.max_
        if self.y_axis.scale == DataScaleType.linear:
            y_min = log(y_min)
            y_max = log(y_max)

        x_range = x_max - x_min
        y_range = y_max - y_min

        canvas_markers = []
        canvas_legend_elements = []
        for seq in self.data:
            # marker 追加
            for x, y in zip(seq.x, seq.y):
                canvas_markers.append(
                    canvas.CanvasMarker(
                        self._abs_to_rel(x, x_range, x_min),
                        self._abs_to_rel(y, y_range, y_min),
                        seq.seq_id
                    )
                )

            # legend 追加
            canvas_legend_elements.append(
                canvas.CanvasLegendElement(seq.seq_id, seq.name)
            )

        canvas_legend = canvas.CanvasLegend(canvas_legend_elements)

        # NOTE: データの min, max をそのまま渡している
        canvas_x_axis = canvas.CanvasAxis(
            self.x_axis.min_,
            self.x_axis.max_,
            canvas.CanvasScaleType.linear if self.x_axis.scale == DataScaleType.linear else canvas.CanvasScaleType.log,
            self.x_axis.name
        )
        canvas_y_axis = canvas.CanvasAxis(
            self.y_axis.min_,
            self.y_axis.max_,
            canvas.CanvasScaleType.linear if self.y_axis.scale == DataScaleType.linear else canvas.CanvasScaleType.log,
            self.y_axis.name
        )
        return canvas.Canvas(
            canvas_markers,
            canvas_x_axis,
            canvas_y_axis,
            canvas_legend
        )

    @staticmethod
    def _abs_to_rel(value: int | float, range_: int | float, min_: int | float) -> float:
        return (value - min_) / range_
