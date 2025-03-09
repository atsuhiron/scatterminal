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
    allow_left_shift: bool = False

    def __len__(self):
        return len(self.label)


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


class _CharField:
    def __init__(self, line_num: int, col_num: int):
        self.char_field: list[list[str]] = [[" " for _c in range(col_num)] for _l in range(line_num)]
        self.cfw_list = []

    def write_marker(self, marker: TerminalMarker):
        if self.char_field[marker.y][marker.x] != " ":
            self.cfw_list.append(
                _CharFieldWarning(
                    "Overlapping markers detected. "
                    "If you need more accurate plot, consider changing the terminal size: (x=%d, y=%d)" % (marker.x, marker.y)
                )
            )
        self.char_field[marker.y][marker.x] = marker.char

    def write_label(self, label: TerminalLabel):
        if label.allow_left_shift and (label.x + len(label)) > len(self.char_field[0]):
            # ラベルの左移動が許可されている and ラベルが右にはみ出ている
            shift = label.x + len(label) - len(self.char_field[0])
            label = TerminalLabel(label.x - shift, label.y, label.label)

        y = label.y
        for i in range(len(label)):
            x = label.x + i
            if self.char_field[y][x] != " ":
                self.cfw_list.append(
                    _CharFieldWarning(
                        "Overlapping labels detected. "
                        "If you need more accurate plot, consider changing the terminal size: (x=%d, y=%d)" % (x, y)
                    )
                )
            self.char_field[y][x] = label.label[i]

    def project(self) -> None:
        for w in self.cfw_list:
            print(w)
        for line in reversed(self.char_field):
            print("".join(line))


@dataclasses.dataclass(frozen=True)
class Terminal(Plottable):
    line_num: int
    col_num: int
    plot_markers: list[TerminalMarker]
    x_axis: TerminalXAxis
    y_axis: TerminalYAxis
    legend: TerminalLegend | None

    @staticmethod
    def get_marker_chars() -> list[str]:
        return ["*", "o", "+", "x", "v", "#", "."]

    def plot(self) -> None:
        cf = _CharField(line_num=self.line_num, col_num=self.col_num)

        # x axis
        for marker in self.x_axis.axis_line:
            cf.write_marker(marker)
        for label in self.x_axis.tick_labels:
            cf.write_label(label)
        if self.x_axis.axis_label:
            cf.write_label(self.x_axis.axis_label)

        # y axis
        for marker in self.y_axis.axis_line:
            cf.write_marker(marker)
        for label in self.y_axis.tick_labels:
            cf.write_label(label)
        for marker in self.y_axis.axis_label or []:
            cf.write_marker(marker)

        # legend
        if self.legend:
            for legend in self.legend.legend_elements:
                cf.write_label(legend)

        # marker
        for marker in self.plot_markers:
            cf.write_marker(marker)

        cf.project()
