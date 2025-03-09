from typing import Type
import abc
import dataclasses
from enum import Enum
import warnings

from common import log, abs_to_rel
import canvas_layer_model as canvas


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
            raise ValueError(
                "length of x and y must be equal: (index={0}, len(x)={1}, len(y)={2})".format(self.seq_id, len(self.x), len(self.y))
            )
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


class DataLegendLoc(str, Enum):
    none = "none"
    lower = "lower"
    right = "right"


@dataclasses.dataclass(frozen=True)
class Data(CanvasConvertible):
    data: list[DataSequence]
    x_axis: DataAxis
    y_axis: DataAxis
    legend_loc: DataLegendLoc

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
        is_x_range_undef = self.x_axis.min_ is None
        if is_x_range_undef:
            # TODO: log の時は正の値だけfilterする
            x_min = min(min(datum.x) for datum in self.data)
            x_max = max(max(datum.x) for datum in self.data)
        else:
            x_min = self.x_axis.min_
            x_max = self.x_axis.max_

        if is_x_range_undef:
            if self.x_axis.scale == DataScaleType.linear:
                white_delta = (x_max - x_min) * 0.08
                canvas_x_range = (x_min - white_delta, x_max + white_delta)
            else:
                white_delta_ratio = log(x_max/x_min) * 0.08
                canvas_x_range = (x_min / white_delta_ratio, x_max * white_delta_ratio)
        else:
            canvas_x_range = (self.x_axis.min_, self.x_axis.max_)

        if self.x_axis.scale == DataScaleType.log:
            x_min = log(x_min)
            x_max = log(x_max)

        x_range = x_max - x_min

        is_y_range_undef = self.y_axis.min_ is None
        if is_y_range_undef:
            y_min = min(min(datum.y) for datum in self.data)
            y_max = max(max(datum.y) for datum in self.data)
        else:
            y_min = self.y_axis.min_
            y_max = self.y_axis.max_

        if is_y_range_undef:
            if self.y_axis.scale == DataScaleType.linear:
                white_delta = (y_max - y_min) * 0.08
                canvas_y_range = (y_min - white_delta, y_max + white_delta)
            else:
                white_delta_ratio = log(y_max/y_min) * 0.08
                canvas_y_range = (y_min / white_delta_ratio, y_max * white_delta_ratio)
        else:
            canvas_y_range = (self.y_axis.min_, self.y_axis.max_)

        if self.y_axis.scale == DataScaleType.log:
            y_min = log(y_min)
            y_max = log(y_max)

        y_range = y_max - y_min

        canvas_markers = []
        canvas_legend_elements = []
        for seq in self.data:
            # marker 追加
            for x, y in zip(seq.x, seq.y):
                canvas_markers.append(
                    canvas.CanvasMarker(
                        abs_to_rel(x, x_range, x_min),
                        abs_to_rel(y, y_range, y_min),
                        seq.seq_id
                    )
                )

            # legend 追加
            canvas_legend_elements.append(
                canvas.CanvasLegendElement(seq.seq_id, seq.name)
            )

        canvas_legend = canvas.CanvasLegend(canvas_legend_elements, canvas.CanvasLegendLoc(self.legend_loc))

        # NOTE: データの min, max をそのまま渡している
        canvas_x_axis = canvas.CanvasAxis(
            canvas_x_range[0],
            canvas_x_range[1],
            canvas.CanvasScaleType.linear if self.x_axis.scale == DataScaleType.linear else canvas.CanvasScaleType.log,
            self.x_axis.name
        )
        canvas_y_axis = canvas.CanvasAxis(
            canvas_y_range[0],
            canvas_y_range[1],
            canvas.CanvasScaleType.linear if self.y_axis.scale == DataScaleType.linear else canvas.CanvasScaleType.log,
            self.y_axis.name
        )
        return canvas.Canvas(
            canvas_markers,
            canvas_x_axis,
            canvas_y_axis,
            canvas_legend
        )
