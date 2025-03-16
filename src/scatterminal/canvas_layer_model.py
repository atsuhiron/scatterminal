from typing import Type
import abc
import dataclasses
from enum import Enum
import shutil
import os
import math
import warnings

from scatterminal.common import log, exp, abs_to_rel
import scatterminal.terminal_layer_model as terminal


def _quantize(rel_value: float, grid_num: int) -> int:
    return round(rel_value * (grid_num - 1))


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


class _TerminalSize:
    def __init__(
            self,
            terminal_size: os.terminal_size,
            y_tick_label_size: int,  # x offset 1
            has_y_axis_label: bool,  # y offset 1
            right_legend_size: int,  # x offset 2
            lower_legend_size: int,  # y offset 2
    ):
        self.terminal_size = terminal_size
        self._has_y_axis_label = has_y_axis_label

        self._tot_y_upper_offset = 1
        self._tot_y_lower_offset = lower_legend_size + 3  # axis_label, empty, tick_label
        self._tot_x_left_offset = y_tick_label_size + int(has_y_axis_label) + 1  # empty
        self._tot_x_right_offset = right_legend_size

    @property
    def lines(self) -> int:
        return self.terminal_size.lines

    @property
    def columns(self) -> int:
        return self.terminal_size.columns

    @property
    def canvas_lines(self) -> int:
        return self.terminal_size.lines - self._tot_y_lower_offset - self._tot_y_upper_offset

    @property
    def canvas_columns(self) -> int:
        return self.terminal_size.columns - self._tot_x_left_offset - self._tot_x_right_offset

    @property
    def has_y_axis_label(self) -> bool:
        return self._has_y_axis_label

    def from_canvas_to_terminal_columns(self, val: int) -> int:
        return val + self._tot_x_left_offset

    def from_canvas_to_terminal_lines(self, val: int) -> int:
        return val + self._tot_y_lower_offset


@dataclasses.dataclass(frozen=True)
class CanvasAxis:
    min_: float
    max_: float
    scale: CanvasScaleType = CanvasScaleType.linear
    name: str | None = None

    def gen_y_axis(
            self,
            label_and_values: list[tuple[str, float]],
            terminal_size: _TerminalSize
    ) -> terminal.TerminalYAxis:
        min_and_max = self._gen_axis_min_max(label_and_values)
        axis_label_offset = int(terminal_size.has_y_axis_label)

        tick_labels = []
        tick_grid_set = set()
        for label, val in label_and_values:
            if self.scale == CanvasScaleType.linear:
                rel = abs_to_rel(val, min_and_max[1] - min_and_max[0], min_and_max[0])
            else:
                rel = abs_to_rel(log(val), log(min_and_max[1]) - log(min_and_max[0]), log(min_and_max[0]))
            quantized = _quantize(rel, terminal_size.canvas_lines)
            terminal_quantized = terminal_size.from_canvas_to_terminal_lines(quantized)
            tick_labels.append(
                terminal.TerminalLabel(axis_label_offset, terminal_quantized, label)
            )
            tick_grid_set.add(quantized)

        axis_lines = []
        for i in range(terminal_size.canvas_lines):
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

        if self.name is None:
            axis_label = None
        else:
            if len(self.name) > terminal_size.canvas_lines:
                raise ValueError("Too large y axis label: size=%d, max=%d" % (len(self.name), terminal_size.canvas_lines))

            start_y = (terminal_size.lines + len(self.name)) // 2
            axis_label = []
            for i in range(len(self.name)):
                axis_label.append(
                    terminal.TerminalMarker(0, start_y - i, self.name[i])
                )
        return terminal.TerminalYAxis(axis_lines, tick_labels, axis_label)

    def gen_x_axis(
            self,
            label_and_values: list[tuple[str, float]],
            terminal_size: _TerminalSize
    ) -> terminal.TerminalXAxis:
        min_and_max = self._gen_axis_min_max(label_and_values)

        tick_labels = []
        tick_grid_set = set()
        for label, val in label_and_values:
            if self.scale == CanvasScaleType.linear:
                rel = abs_to_rel(val, min_and_max[1] - min_and_max[0], min_and_max[0])
            else:
                rel = abs_to_rel(log(val), log(min_and_max[1]) - log(min_and_max[0]), log(min_and_max[0]))
            quantized = _quantize(rel, terminal_size.canvas_columns)
            terminal_quantized_shifted = terminal_size.from_canvas_to_terminal_columns(quantized) - len(label) // 2
            tick_labels.append(
                terminal.TerminalLabel(
                    terminal_quantized_shifted,
                    terminal_size.from_canvas_to_terminal_lines(-1),
                    label,
                    allow_left_shift=True
                )
            )
            tick_grid_set.add(quantized)

        axis_lines = []
        for i in range(terminal_size.canvas_columns):
            if i in tick_grid_set:
                char = "+"
            else:
                char = "-"
            axis_lines.append(
                terminal.TerminalMarker(
                    terminal_size.from_canvas_to_terminal_columns(i),
                    terminal_size.from_canvas_to_terminal_lines(0),
                    char
                )
            )

        if self.name is None:
            axis_label = None
        else:
            if len(self.name) > terminal_size.canvas_columns:
                raise ValueError("Too large x axis label: size=%d, max=%d" % (len(self.name), terminal_size.canvas_columns))
            canvas_center_x = terminal_size.from_canvas_to_terminal_columns(terminal_size.canvas_columns // 2) - len(self.name) // 2
            axis_label = terminal.TerminalLabel(canvas_center_x, terminal_size.from_canvas_to_terminal_lines(-2), self.name)
        return terminal.TerminalXAxis(axis_lines, tick_labels, axis_label)

    def calc_tick(self, primary_limit: int = 20, secondary_limit: int = 10) -> list[tuple[str, float]]:
        min_and_max = (self.min_, self.max_)
        if self.scale == CanvasScaleType.linear:
            ticks = self._calc_linear_tick(*min_and_max, *(primary_limit, secondary_limit))
        else:
            ticks = self._calc_log_tick(*min_and_max, *(primary_limit, secondary_limit))

        use_index = self._use_index(*min_and_max)
        sd = self._calc_significant_digits(*min_and_max)
        format_ = "e" if use_index else "f"
        return [(f"{tick:.{sd}{format_}}", tick) for tick in ticks]

    @staticmethod
    def _calc_linear_tick(min_: float, max_: float, primary_limit: int, secondary_limit: int) -> list[float]:
        value_range = max_ - min_
        tick_scale = exp(round(log(value_range) - 1))
        tick_num = value_range / tick_scale
        if tick_num > primary_limit:
            tick_scale *= 5
            tick_num /= 5
        elif tick_num > secondary_limit:
            tick_scale *= 2.5
            tick_num /= 2.5
        tick_num = int(math.ceil(tick_num))

        min_tick = round(min_ / tick_scale) * tick_scale
        return [min_tick + (i * tick_scale) for i in range(tick_num)]

    @staticmethod
    def _calc_log_tick(min_: float, max_: float, primary_limit: int, secondary_limit: int) -> list[float]:
        value_range = log(max_) - log(min_)
        tick_scale = exp(round(log(value_range) - 1))
        tick_num = value_range / tick_scale
        if tick_num > primary_limit:
            tick_scale *= 5
            tick_num /= 5
        elif tick_num > secondary_limit:
            tick_scale *= 2.5
            tick_num /= 2.5
        tick_num = int(math.ceil(tick_num))

        min_tick = round(log(min_) / tick_scale) * tick_scale
        return [exp(min_tick + (i * tick_scale)) for i in range(tick_num)]

    @staticmethod
    def _calc_significant_digits(min_: float, max_: float) -> int:
        delta = max_ - min_
        inv_med = 2/(abs(min_) + abs(max_))

        raw_digit = log(delta * inv_med) + 2
        if raw_digit < 1:
            return 1
        if raw_digit > 6:
            return 6
        return int(math.ceil(raw_digit))

    def _use_index(self, min_: float, max_: float) -> bool:
        far_from_origin = abs(min_) if abs(min_) > abs(max_) else abs(max_)
        nea_from_origin = abs(min_) if abs(min_) < abs(max_) else abs(max_)

        if self.scale == CanvasScaleType.linear:
            median_order = log((far_from_origin + nea_from_origin) / 2)
        else:
            median_order = log(math.sqrt(far_from_origin * nea_from_origin))

        return median_order > 4 or median_order < -4

    def _gen_axis_min_max(self, label_and_values: list[tuple[str, float]]) -> tuple[float, float]:
        return (
            min(min(lv[1] for lv in label_and_values), self.min_),
            max(max(lv[1] for lv in label_and_values), self.max_),
        )


@dataclasses.dataclass(frozen=True)
class CanvasLegendElement:
    marker_group_id: int
    sequence_name: str | None


class CanvasLegendLoc(str, Enum):
    none = "none"
    lower = "lower"
    right = "right"


@dataclasses.dataclass(frozen=True)
class CanvasLegend:
    legend_elements: list[CanvasLegendElement]
    loc: CanvasLegendLoc

    def gen_right_legend(self, marker_char_dict: dict[int, str]) -> tuple[tuple[int, int], terminal.TerminalLegend]:
        legend_element_strings = [f"{marker_char_dict[le.marker_group_id]}: {le.sequence_name}" for le in self.legend_elements]
        max_legend_size = max(map(len, legend_element_strings))

        _terminal_size = shutil.get_terminal_size()
        legend_labels = []
        for i_line in range(len(legend_element_strings)):
            x = _terminal_size.columns - max_legend_size
            y = _terminal_size.lines - i_line - 2
            legend_labels.append(
                terminal.TerminalLabel(x, y, legend_element_strings[i_line])
            )

        return (max_legend_size, 0), terminal.TerminalLegend(legend_labels)

    def gen_lower_legend(self, marker_char_dict: dict[int, str]) -> tuple[tuple[int, int], terminal.TerminalLegend]:
        legend_element_strings = [f"{marker_char_dict[le.marker_group_id]}: {le.sequence_name}" for le in self.legend_elements]
        max_legend_size = max(map(len, legend_element_strings))

        space = 2
        _terminal_size = shutil.get_terminal_size()
        max_legend_num_per_line = _terminal_size.columns // (max_legend_size + space)  # 1行に表示できる最大legend数
        legend_line_num = int(math.ceil(len(legend_element_strings) / max_legend_num_per_line))
        legend_labels = []
        for i_line in range(legend_line_num):
            y = legend_line_num - i_line - 1
            x = 0
            for j_legend in range(max_legend_num_per_line):
                index = max_legend_num_per_line * i_line + j_legend
                if index >= len(legend_element_strings):
                    # end line
                    break
                legend = legend_element_strings[index]
                legend_labels.append(
                    terminal.TerminalLabel(x, y, legend)
                )
                x += len(legend) + space

        return (0, legend_line_num), terminal.TerminalLegend(legend_labels)


@dataclasses.dataclass(frozen=True)
class Canvas(TerminalConvertible):
    markers: list[CanvasMarker]
    x_axis: CanvasAxis
    y_axis: CanvasAxis
    legend: CanvasLegend

    def to_terminal(self, plot_type: Type[terminal.Plottable]) -> terminal.Plottable:
        # generate marker dict
        marker_char_dict = self._gen_marker_char_dict(set(marker.marker_group_id for marker in self.markers), plot_type.get_marker_chars())

        # generate legend
        if self.legend.loc == CanvasLegendLoc.right:
            legend_offsets, terminal_legend = self.legend.gen_right_legend(marker_char_dict)
        elif self.legend.loc == CanvasLegendLoc.lower:
            legend_offsets, terminal_legend = self.legend.gen_lower_legend(marker_char_dict)
        else:
            legend_offsets: tuple[int, int] = 0, 0
            terminal_legend = None

        # generate y axis
        tick_label_and_values_y = self.y_axis.calc_tick()
        max_label_size_y = max(len(tick_label_and_value[0]) for tick_label_and_value in tick_label_and_values_y)
        terminal_size = _TerminalSize(shutil.get_terminal_size(), max_label_size_y, self.y_axis.name is not None, *legend_offsets)
        terminal_y_axis = self.y_axis.gen_y_axis(tick_label_and_values_y, terminal_size)

        # generate x axis
        primary, secondary = 18, 8
        tick_label_and_values_x = self.x_axis.calc_tick()
        total_label_size_x = sum(len(tick_label_and_value[0]) for tick_label_and_value in tick_label_and_values_x)
        while total_label_size_x > (terminal_size.columns / 2):
            primary -= 1
            secondary -= 1
            tick_label_and_values_x = self.x_axis.calc_tick(primary, secondary)
            total_label_size_x = sum(len(tick_label_and_value[0]) for tick_label_and_value in tick_label_and_values_x)
        terminal_x_axis = self.x_axis.gen_x_axis(tick_label_and_values_x, terminal_size)

        # generate marker
        terminal_markers = []
        for marker in self.markers:
            x = _quantize(marker.x, terminal_size.canvas_columns)
            y = _quantize(marker.y, terminal_size.canvas_lines)
            terminal_mark = terminal.TerminalMarker(
                x=terminal_size.from_canvas_to_terminal_columns(x),
                y=terminal_size.from_canvas_to_terminal_lines(y),
                char=marker_char_dict[marker.marker_group_id]
            )
            terminal_markers.append(terminal_mark)

        return terminal.Terminal(
            terminal_size.lines, terminal_size.columns,
            terminal_markers, terminal_x_axis, terminal_y_axis, terminal_legend
        )

    @staticmethod
    def _gen_marker_char_dict(marker_group_ids: set[int], chars: list[str]) -> dict[int, str]:
        char_num = len(chars)
        if len(marker_group_ids) > char_num:
            warnings.warn("The number of data series exceeds the number of marker types available. "
                          "Then, Markers are reused making data identification difficult.", UserWarning)

        char_dict = {}
        for gid in marker_group_ids:
            char_dict[gid] = chars[gid % char_num]
        return char_dict
