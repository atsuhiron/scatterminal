import dataclasses


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


@dataclasses.dataclass(frozen=True)
class TerminalXAxis:
    axis_line: list[TerminalMarker]
    tick_labels: list[TerminalLabel]
    axis_label: TerminalLabel | None = None


@dataclasses.dataclass(frozen=True)
class TerminalYAxis:
    axis_line = list[TerminalMarker]
    tick_labels: list[TerminalLabel]
    axis_label: list[TerminalMarker] | None = None


@dataclasses.dataclass(frozen=True)
class TerminalLegend:
    legend_elements: list[TerminalLabel]


@dataclasses.dataclass(frozen=True)
class Terminal:
    plot_markers: list[TerminalMarker]
    x_axis: TerminalXAxis
    y_axis: TerminalYAxis
    legend: TerminalLegend
    