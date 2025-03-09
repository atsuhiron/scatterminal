from __future__ import annotations
import abc
import dataclasses


class Plottable(metaclass=abc.ABCMeta):
    @staticmethod
    def get_marker_chars() -> list[str]:
        pass

    @abc.abstractmethod
    def plot(self) -> None:
        pass


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
class TerminalPoint:
    x: int
    y: int

    def __post_init__(self):
        if self.x < 0:
            raise ValueError("Terminal point coordination should be positive: x")
        if self.y < 0:
            raise ValueError("Terminal point coordination should be positive: y")


@dataclasses.dataclass(frozen=True)
class TerminalMarker(TerminalPoint):
    char: str

    def __post_init__(self):
        if len(self.char) != 1:
            raise ValueError("Length of Marker char should be 1")


@dataclasses.dataclass(frozen=True)
class TerminalLabel(TerminalPoint):
    label: str

    def __len__(self):
        return len(self.label)

    def get_relative_start_point(self) -> int:
        return -(len(self) // 2)


@dataclasses.dataclass(frozen=True)
class TerminalXAxis:
    axis_line: list[TerminalMarker]
    tick_labels: list[TerminalLabel]
    axis_label: TerminalLabel | None = None


@dataclasses.dataclass(frozen=True)
class TerminalYAxis:
    axis_line: list[TerminalMarker]
    tick_labels: list[TerminalLabel]
    axis_label: list[TerminalMarker] | None = None


@dataclasses.dataclass(frozen=True)
class TerminalLegend:
    legend_elements: list[TerminalLabel]


@dataclasses.dataclass(frozen=True)
class Terminal(Plottable):
    plot_markers: list[TerminalMarker]
    x_axis: TerminalXAxis
    y_axis: TerminalYAxis
    legend: TerminalLegend | None

    @staticmethod
    def get_marker_chars() -> list[str]:
        return ["*", "o", "+", "x", "v", "#", "."]

    def plot(self) -> None:
        pass
