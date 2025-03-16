from __future__ import annotations

from typing import Callable, Type
import abc
import dataclasses
from enum import Enum
import warnings

from scatterminal.common import log, abs_to_rel
import scatterminal.canvas_layer_model as canvas


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
    x_name: str | None = None

    def __post_init__(self):
        if len(self.x) != len(self.y):
            raise ValueError(
                "length of x and y must be equal: (seq_id={0}, len(x)={1}, len(y)={2})".format(self.seq_id, len(self.x), len(self.y))
            )
        if not all(map(lambda x: isinstance(x, (int, float)), self.x)):
            raise TypeError("x must be list[int | float]: seq_id={0}".format(self.seq_id))
        if not all(map(lambda y: isinstance(y, (int, float)), self.y)):
            raise TypeError("y must be list[int | float]: seq_id={0}".format(self.seq_id))
        if (self.name is not None) and (not self.name.isascii()):
            raise ValueError("Sequence name must be ascii: seq_id={0}".format(self.seq_id))
        if (self.x_name is not None) and (not self.x_name.isascii()):
            raise ValueError("Sequence x_name must be ascii: seq_id={0}".format(self.seq_id))

    def create_filtered(self, filter_func: Callable[[tuple[int | float, int | float]], bool]) -> DataSequence:
        new_x = []
        new_y = []
        for xy_pair in filter(filter_func, zip(self.x, self.y)):
            new_x.append(xy_pair[0])
            new_y.append(xy_pair[1])
        return DataSequence(new_x, new_y, self.seq_id, self.name)


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
            raise ValueError("Axis name must be ascii: %s" % self.name)
        if (self.min_ is None) != (self.max_ is None):
            raise ValueError("Axis min and Axis max should be defined simultaneously: (min, max)=(%s, %s)" % (self.min_, self.max_))
        if (self.min_ is not None) and (self.max_ is not None) and self.min_ >= self.max_:
            raise ValueError("Axis min is larger than max: (min, max)=(%f, %f)" % (self.min_, self.max_))
        if self.scale == DataScaleType.log:
            if (self.min_ is not None) and (self.min_ <= 0):
                raise ValueError("Axis min must be positive value on log-scale")


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
                    warnings.warn(
                        "Non-positive value is detected on log-scale x axis. This data point is not plotted.: seq_id=%d" % datum.seq_id,
                        UserWarning
                    )
        if self.y_axis.scale == DataScaleType.log:
            for datum in self.data:
                if min(datum.y) <= 0:
                    warnings.warn(
                        "Non-positive value is detected on log-scale y axis. This data point is not plotted.: seq_id=%d" % datum.seq_id,
                        UserWarning
                    )

    def to_canvas(self, canvas_type: Type[canvas.TerminalConvertible]) -> canvas.TerminalConvertible:
        # positive-pass filter
        if self.x_axis.scale == DataScaleType.log:
            filtered_data = [datum.create_filtered(lambda xy: xy[0] > 0) for datum in self.data]
        else:
            filtered_data = self.data

        if self.y_axis.scale == DataScaleType.log:
            filtered_data = [datum.create_filtered(lambda xy: xy[1] > 0) for datum in filtered_data]
        else:
            filtered_data = filtered_data

        is_x_range_undef = self.x_axis.min_ is None
        if is_x_range_undef:
            x_min = min(min(datum.x) for datum in filtered_data)
            x_max = max(max(datum.x) for datum in filtered_data)
        else:
            x_min = self.x_axis.min_
            x_max = self.x_axis.max_
        
        edge_space_ratio = 0.1

        if is_x_range_undef:
            if self.x_axis.scale == DataScaleType.linear:
                white_delta = (x_max - x_min) * edge_space_ratio
                canvas_x_range = (x_min - white_delta, x_max + white_delta)
            else:
                white_delta_ratio = log(x_max/x_min) * edge_space_ratio
                canvas_x_range = (x_min / white_delta_ratio, x_max * white_delta_ratio)
        else:
            canvas_x_range = (self.x_axis.min_, self.x_axis.max_)

        is_y_range_undef = self.y_axis.min_ is None
        if is_y_range_undef:
            y_min = min(min(datum.y) for datum in filtered_data)
            y_max = max(max(datum.y) for datum in filtered_data)
        else:
            y_min = self.y_axis.min_
            y_max = self.y_axis.max_

        if is_y_range_undef:
            if self.y_axis.scale == DataScaleType.linear:
                white_delta = (y_max - y_min) * edge_space_ratio
                canvas_y_range = (y_min - white_delta, y_max + white_delta)
            else:
                white_delta_ratio = (log(y_max/y_min) * edge_space_ratio) + 1
                canvas_y_range = (y_min / white_delta_ratio, y_max * white_delta_ratio)
        else:
            canvas_y_range = (self.y_axis.min_, self.y_axis.max_)

        canvas_markers = []
        canvas_legend_elements = []
        x_process_func = log if self.x_axis.scale == DataScaleType.log else lambda v: v
        y_process_func = log if self.y_axis.scale == DataScaleType.log else lambda v: v

        for seq in filtered_data:
            # marker 追加
            for x, y in zip(seq.x, seq.y):
                canvas_markers.append(
                    canvas.CanvasMarker(
                        abs_to_rel(
                            x_process_func(x),
                            x_process_func(canvas_x_range[1]) - x_process_func(canvas_x_range[0]),
                            x_process_func(canvas_x_range[0])
                        ),
                        abs_to_rel(
                            y_process_func(y),
                            y_process_func(canvas_y_range[1]) - y_process_func(canvas_y_range[0]),
                            y_process_func(canvas_y_range[0])
                        ),
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
