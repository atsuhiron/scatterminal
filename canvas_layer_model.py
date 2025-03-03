from typing import Type
import abc
import dataclasses
from enum import Enum
import shutil
import os
import math

from common import log, exp, abs_to_rel
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


class _TerminalSize:
    y_offset = 3  # axis_label, empty, tick_label

    def __init__(
            self,
            terminal_size: os.terminal_size,
            y_tick_label_size: int,
            has_y_axis_label: bool
    ):
        self.terminal_size = terminal_size
        self.y_tick_label_size = y_tick_label_size
        self.has_y_axis_label = has_y_axis_label

    @property
    def lines(self) -> int:
        return self.terminal_size.lines

    @property
    def columns(self) -> int:
        return self.terminal_size.columns

    @property
    def canvas_lines(self) -> int:
        return self.terminal_size.lines - self.y_offset

    @property
    def canvas_columns(self) -> int:
        return self.terminal_size.columns - self.y_tick_label_size - int(self.has_y_axis_label) - 1  # empty

    def from_canvas_to_terminal_columns(self, val: int) -> int:
        return val + self.y_tick_label_size + int(self.has_y_axis_label) + 1

    def from_canvas_to_terminal_lines(self, val: int) -> int:
        return val + self.y_offset


@dataclasses.dataclass(frozen=True)
class Canvas(TerminalConvertible):
    markers: list[CanvasMarker]
    x_axis: CanvasAxis
    y_axis: CanvasAxis
    legend: CanvasLegend

    def to_terminal(self, plot_type: Type[terminal.Plottable]) -> terminal.Plottable:
        tick_label_and_values_y = self.calc_y_tick(self.y_axis)
        max_label_size_y = max(len(tick_label_and_value[0]) for tick_label_and_value in tick_label_and_values_y)
        terminal_size = _TerminalSize(shutil.get_terminal_size(), max_label_size_y, self.y_axis.name is not None)
        terminal_y_axis = self.gen_y_axis(tick_label_and_values_y, self.y_axis, terminal_size)

        char_field = _CharField(terminal_size.columns, terminal_size.lines)

    @staticmethod
    def gen_y_axis(
            label_and_values: list[tuple[str, float]],
            canvas_axis: CanvasAxis,
            terminal_size: _TerminalSize
    ) -> terminal.TerminalYAxis:
        min_and_max = (canvas_axis.min_, canvas_axis.max_)
        axis_label_offset = int(terminal_size.has_y_axis_label)

        tick_labels = []
        tick_grid_set = set()
        for label, val in label_and_values:
            if canvas_axis.scale == CanvasScaleType.linear:
                rel = abs_to_rel(val, min_and_max[1] - min_and_max[0], min_and_max[0])
            else:
                rel = abs_to_rel(log(val), log(min_and_max[1]) - log(min_and_max[0]), log(min_and_max[0]))
            quantized = Canvas.quantize(rel, terminal_size.canvas_lines)
            terminal_quantized = terminal_size.from_canvas_to_terminal_lines(quantized)
            tick_labels.append(
                terminal.TerminalLabel(axis_label_offset, terminal_quantized, label)
            )
            tick_grid_set.add(quantized)

        axis_lines = []
        for i in range(terminal_size.lines):
            if i in tick_grid_set:
                char = "+"
            else:
                char = "|"
            axis_lines.append(
                terminal.TerminalMarker(
                    terminal_size.from_canvas_to_terminal_columns(0),
                    terminal_size.from_canvas_to_terminal_lines(i),
                    char
                )
            )

        if canvas_axis.name is None:
            axis_label = None
        else:
            if terminal_size.lines < len(canvas_axis.name):
                raise ValueError("Too large y axis label: size=%d, max=%d" % (len(canvas_axis.name), terminal_size.lines))

            start_y = (terminal_size.lines // 2) - len(canvas_axis.name) // 2
            axis_label = []
            for i in range(len(canvas_axis.name)):
                axis_label.append(
                    terminal.TerminalMarker(0, start_y + i, canvas_axis.name[i])
                )
        return terminal.TerminalYAxis(axis_lines, tick_labels, axis_label)


    @staticmethod
    def calc_y_tick(canvas_axis: CanvasAxis) -> list[tuple[str, float]]:
        min_and_max = (canvas_axis.min_, canvas_axis.max_)
        if canvas_axis.scale == CanvasScaleType.linear:
            ticks = Canvas._calc_linear_tick(*min_and_max)
        else:
            ticks = Canvas._calc_log_tick(*min_and_max)

        use_index = Canvas._use_index(canvas_axis.scale, *min_and_max)
        if use_index:
            sd = Canvas._calc_significant_digits(*min_and_max)
            return [(f"{tick:.{sd}e}", tick) for tick in ticks]
        return [(f"{tick:f}", tick) for tick in ticks]

    @staticmethod
    def _calc_linear_tick(min_: float, max_: float) -> list[float]:
        value_range = max_ - min_
        tick_scale = exp(round(log(value_range) - 1))
        tick_num = value_range / tick_scale
        if tick_num > 20:
            tick_scale *= 5
            tick_num /= 5
        elif tick_num > 10:
            tick_scale *= 2.5
            tick_num /= 2.5
        tick_num = int(math.ceil(tick_num))

        min_tick = round(min_ / tick_scale) * tick_scale
        return [min_tick + (i * tick_scale) for i in range(tick_num)]

    @staticmethod
    def _calc_log_tick(min_: float, max_: float) -> list[float]:
        value_range = log(max_) - log(min_)
        tick_scale = exp(round(log(value_range) - 2))
        tick_num = value_range / tick_scale
        if tick_num > 20:
            tick_scale *= 5
            tick_num /= 5
        elif tick_num > 10:
            tick_scale *= 2.5
            tick_num /= 2.5
        tick_num = int(math.ceil(tick_num))

        min_tick = round(log(min_) / tick_scale) * tick_scale
        return [exp(min_tick + (i * tick_scale)) for i in range(tick_num)]

    @staticmethod
    def _calc_significant_digits(min_: float, max_: float) -> int:
        return int(math.ceil(log(max_ - min_)))

    @staticmethod
    def _use_index(scale: CanvasScaleType, min_: float, max_: float) -> bool:
        far_from_origin = abs(min_) if abs(min_) > abs(max_) else abs(max_)
        nea_from_origin = abs(min_) if abs(min_) < abs(max_) else abs(max_)

        if scale == CanvasScaleType.linear:
            median_order = log((far_from_origin + nea_from_origin) / 2)
        else:
            median_order = log(math.sqrt(far_from_origin * nea_from_origin))

        return median_order > 4 or median_order < -4

    @staticmethod
    def quantize(rel_value: float, grid_num: int) -> int:
        return round(rel_value * grid_num)


if __name__ == "__main__":
    for _min, _max, _scale in [
        (0.12, 13.4, "linear"),
        (-13.1, 25.3, "linear"),
        (-13.1, -0.3, "linear"),
        (140.001, 140.029, "linear"),
        (0.12, 1003.7, "log"),
    ]:
        ca = CanvasAxis(_min, _max, CanvasScaleType(_scale))
        Canvas.calc_y_tick(ca, shutil.get_terminal_size())
