from typing import TextIO

from scatterminal.data_layer_model import DataSequence

ValueType = str | int | float


def read_file(file_obj: TextIO, ext: str, sep: str | None) -> list[list[str]]:
    if sep is None:
        if ext == "csv":
            sep = ","
        elif ext == "tsv":
            sep = "\t"
        else:
            raise ValueError("Failed to estimate separator character. Please specify sep explicitly.")

    lines = file_obj.readlines()

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
        raise TypeError("int or float type are only available.")


def _has_header(column: list[ValueType]) -> bool:
    return isinstance(column[0], str)


def parse(str_cells: list[list[str]], next_id: int) -> list[DataSequence]:
    _check_col_num(str_cells)
    # parse and transpose
    parsed_cells = [[_parse_cell(line[i]) for line in str_cells] for i in range(len(str_cells[0]))]

    _ = tuple(_check_col_type(col) for col in parsed_cells)
    col_num = len(parsed_cells)

    has_header = any(_has_header(col) for col in parsed_cells)
    header_line = str_cells[0] if has_header else [None] * col_num
    content_slice = slice(int(has_header), None)

    if col_num == 1:
        content = parsed_cells[0][content_slice]
        return [DataSequence(list(range(len(content))), content, next_id, header_line[0], None)]
    return [
        DataSequence(
            parsed_cells[0][content_slice],
            parsed_cells[i][content_slice],
            next_id + i - 1,
            header_line[i],
            header_line[0]
        ) for i in range(1, col_num)
    ]
