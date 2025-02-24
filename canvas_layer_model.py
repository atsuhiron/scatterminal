from typing import Type
import abc
import dataclasses
from enum import Enum
import shutil
import math

from common import log, exp
import terminal_layer_model as terminal


class TerminalConvertible(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_terminal(self, plot_type: Type[terminal.Plottable]) -> terminal.Plottable:
        pass


@dataclasses.dataclass(frozen=True)
class CanvasPoint:
    x: float
    y: float


@dataclasses.dataclass(frozen=True)
class CanvasMarker(CanvasPoint):
    marker_group_id: int


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
    marker_group_id: int
    sequence_name: str | None


@dataclasses.dataclass(frozen=True)
class CanvasLegend:
    legend_elements: list[CanvasLegendElement]


class _CharFieldWarning(str):
    pass


class _CharField:
    def __init__(self, col_num: int, line_num: int):
        self.char_field = [["" for _c in range(col_num)] for _l in range(line_num)]

    def write(self, char: str, col: int, line: int) -> list[_CharFieldWarning]:
        cfw_list = []
        if self.char_field[line][col]:
            cfw = _CharFieldWarning("Overlapping markers detected. If you need more accurate plot, consider changing the terminal size.")
            cfw_list.append(cfw)
        self.char_field[line][col] = char
        return cfw_list


@dataclasses.dataclass(frozen=True)
class Canvas(TerminalConvertible):
    markers: list[CanvasMarker]
    x_axis: CanvasAxis
    y_axis: CanvasAxis
    legend: CanvasLegend

    def to_terminal(self, plot_type: Type[terminal.Plottable]) -> terminal.Plottable:
        terminal_size = shutil.get_terminal_size()
        char_field = _CharField(terminal_size.columns, terminal_size.lines)

    @staticmethod
    def calc_y_tick(canvas_axis: CanvasAxis) -> list[terminal.TerminalLabel]:
        if canvas_axis.scale == CanvasScaleType.linear:
            detail_hierarchy = [[1., 10.], [5.], [2.5, 7.5]]
        else:
            detail_hierarchy = [[1., 10.], [3.], [2., 6.]]
        detail_log_hierarchy = [(prior, [log(v) for v in h]) for (prior, h) in enumerate(detail_hierarchy)]

        if canvas_axis.min_ > 0:
            min_sign = 1.0
            min_order = log(canvas_axis.min_)
        else:
            min_sign = -1.0
            min_order = log(math.fabs(canvas_axis.min_))

        if canvas_axis.max_ > 0:
            max_sign = 1.0
            max_order = log(canvas_axis.max_)
        else:
            max_sign = -1.0
            max_order = log(math.fabs(canvas_axis.max_))

        min_max_digit = log(canvas_axis.max_ - canvas_axis.min_)
        if min_order > max_order:
            # min is large negative number
            actual_max_order = min_order + min_max_digit
            actual_min_order = min_order
        else:
            # max is large positive number
            actual_max_order = max_order
            actual_min_order = max_order - min_max_digit

        print(actual_min_order, actual_max_order)


if __name__ == "__main__":
    ca = CanvasAxis(0.12, 13.4, CanvasScaleType.linear)
    Canvas.calc_y_tick(ca)
