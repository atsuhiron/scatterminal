import dataclasses

from data_layer_model import DataScaleType, DataAxis, DataSequence, Data, DataLegendLoc
from canvas_layer_model import Canvas
from terminal_layer_model import Terminal


ValueType = str | int | float


@dataclasses.dataclass(frozen=True)
class PlotParameter:
    x_scale: DataScaleType
    y_scale: DataScaleType


def _read_file(file_name: str, sep: str | None) -> list[list[str]]:
    if sep is None:
        ext = file_name.split(".")[-1]
        if ext == "csv":
            sep = ","
        elif ext == "tsv":
            sep = "t"
        else:
            raise ValueError("Failed to estimate separator character. Please specify sep explicitly.")

    with open(file_name, "r") as f:
        lines = f.readlines()

    cell_lines = []
    for line in lines:
        cells = [cell.strip() for cell in line.split(sep)]
        cell_lines.append(cells)
    return cell_lines


def _parse_cell(v: str) -> ValueType:
    if len(v) == 0:
        return float("nan")
    if v.isalpha():
        return v
    if v.isdigit():
        return int(v)
    try:
        return float(v)
    except ValueError:
        return v


def _check_col_num(str_cells: list[list[str]]):
    column_nums = set(len(line) for line in str_cells)
    if len(column_nums) != 1:
        raise ValueError("The length of column is not aligned.")


def _check_col_type(column: list[ValueType]):
    if isinstance(column[0], str):
        value_column = column[1:]
    else:
        value_column = column

    numeric_type_set = {float, int}
    type_set = set(type(cell) for cell in value_column)
    if not type_set.issubset(numeric_type_set):
        raise ValueError("int or float type are only available.")


def _has_header(column: list[ValueType]) -> bool:
    return isinstance(column[0], str)


def _parse(str_cells: list[list[str]], next_id: int) -> list[DataSequence]:
    _check_col_num(str_cells)
    # parse and transpose
    parsed_cells = [[_parse_cell(line[i]) for line in str_cells] for i in range(len(str_cells[0]))]

    _ = (_check_col_type(col) for col in parsed_cells)
    col_num = len(parsed_cells)

    has_header = any(_has_header(col) for col in parsed_cells)
    header_line = str_cells[0] if has_header else [None] * col_num
    content_slice = slice(int(has_header), None)

    if col_num == 1:
        content = parsed_cells[0][content_slice]
        return [DataSequence(list(range(len(content))), content, next_id, header_line[0])]
    return [
        DataSequence(
            parsed_cells[0][content_slice],
            parsed_cells[i][content_slice],
            next_id + i - 1,
            header_line[i]
        ) for i in range(1, col_num)
    ]


def plot_csv(
        file_names: list[str],
        sep: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        x_scale: str = "linear",
        y_scale: str = "linear",
        x_lim: tuple[float, float] | None = None,
        y_lim: tuple[float, float] | None = None,
        legend_loc: str = "right"
) -> None:
    next_id = 0
    data_sequences = []
    for file_name in file_names:
        str_cells = _read_file(file_name, sep)
        data_sequences.extend(_parse(str_cells, next_id))
        next_id = len(data_sequences)
    x_lim = (None, None) if x_lim is None else x_lim
    x_axis = DataAxis(DataScaleType(x_scale), x_label, x_lim[0], x_lim[1])
    y_lim = (None, None) if y_lim is None else y_lim
    y_axis = DataAxis(DataScaleType(y_scale), y_label, y_lim[0], y_lim[1])

    data = Data(data_sequences, x_axis, y_axis, DataLegendLoc(legend_loc))
    canvas = data.to_canvas(Canvas)
    terminal = canvas.to_terminal(Terminal)
    terminal.plot()


if __name__ == "__main__":
    plot_csv(["samples/sample_double_column.csv"])
