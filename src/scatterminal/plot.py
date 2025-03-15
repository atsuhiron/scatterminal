import argparse
import dataclasses


from scatterminal.canvas_layer_model import Canvas
from scatterminal.csv_parser import read_file, parse
from scatterminal.data_layer_model import DataScaleType, DataAxis, Data, DataLegendLoc
from scatterminal.terminal_layer_model import Terminal


@dataclasses.dataclass(frozen=True)
class PlotParameter:
    x_scale: DataScaleType
    y_scale: DataScaleType


def plot_csv(
        file_paths: list[str],
        sep: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        x_scale: str = "linear",
        y_scale: str = "linear",
        x_lim: tuple[float, float] | None = None,
        y_lim: tuple[float, float] | None = None,
        legend_loc: str = "lower"
) -> None:
    next_id = 0
    data_sequences = []
    for file_path in file_paths:
        with open(file_path, "r") as f:
            str_cells = read_file(f, file_path.split(".")[-1], sep)
        data_sequences.extend(parse(str_cells, next_id))
        next_id = len(data_sequences)

    if x_label is None:
        x_labels = set(seq.x_name for seq in data_sequences)
        if len(x_labels) == 1:
            x_label = x_labels.pop()
    if y_label is None:
        y_labels = set(seq.name for seq in data_sequences)
        if len(y_labels) == 1:
            y_label = y_labels.pop()

    x_lim = (None, None) if x_lim is None else x_lim
    x_axis = DataAxis(DataScaleType(x_scale), x_label, x_lim[0], x_lim[1])
    y_lim = (None, None) if y_lim is None else y_lim
    y_axis = DataAxis(DataScaleType(y_scale), y_label, y_lim[0], y_lim[1])

    data = Data(data_sequences, x_axis, y_axis, DataLegendLoc(legend_loc))
    canvas = data.to_canvas(Canvas)
    terminal_ = canvas.to_terminal(Terminal)
    terminal_.plot()


def main():
    parser = argparse.ArgumentParser(
        prog="scatterminal",
        description="Plot scatter plot on terminal",
    )
    parser.add_argument(
        "file_path",
        nargs="*",
        help="File path to plot (multiple designations possible)"
    )
    parser.add_argument(
        "--sep",
        help="Separator character. If not specified, it is inferred from the extension."
    )
    parser.add_argument(
        "--xscale",
        choices=[scale.value for scale in DataScaleType],
        help="Scale type of x axis",
        default="linear"
    )
    parser.add_argument(
        "--yscale",
        choices=[scale.value for scale in DataScaleType],
        help="Scale type of y axis",
        default="linear"
    )
    parser.add_argument(
        "--xlabel",
        help="Label of x axis"
    )
    parser.add_argument(
        "--ylabel",
        help="Label of y axis"
    )
    parser.add_argument(
        "--xlim",
        nargs=2,
        type=float,
        metavar=("X_MIN", "X_MAX"),
        help="Range of x axis (specify both X_MIN and X_MAX)"
    )
    parser.add_argument(
        "--ylim",
        nargs=2,
        type=float,
        metavar=("Y_MIN", "Y_MAX"),
        help="Range of axis (specify both Y_MIN and Y_MAX)"
    )
    parser.add_argument(
        "--legend-loc",
        choices=[loc.value for loc in DataLegendLoc],
        help="Position of legend",
        default="lower"
    )

    argv = parser.parse_args()
    plot_csv(
        file_paths=argv.file_path,
        sep=argv.sep,
        x_label=argv.xlabel,
        y_label=argv.ylabel,
        x_scale=argv.xscale,
        y_scale=argv.yscale,
        x_lim=argv.xlim,
        y_lim=argv.ylim,
        legend_loc=argv.legend_loc
    )


if __name__ == "__main__":
    plot_csv(["../../tests/samples/double_column.csv"])