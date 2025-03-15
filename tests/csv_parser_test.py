from io import StringIO

import pytest

from scatterminal.csv_parser import read_file, parse
from scatterminal.data_layer_model import DataSequence


def test_read_file_csv():
    file_obj = StringIO(
        "x,y,z\n"
        "0,1,3\n"
        "2,1,8\n"
        "4,2,13\n"
    )
    expected = [
        ["x", "y", "z"],
        ["0", "1", "3"],
        ["2", "1", "8"],
        ["4", "2", "13"],
    ]
    actual = read_file(file_obj, "csv", None)
    assert expected == actual


def test_read_file_csv_specified_sep():
    file_obj = StringIO(
        "x,y,z\n"
        "0,1,3\n"
        "2,1,8\n"
        "4,2,13\n"
    )
    expected = [
        ["x", "y", "z"],
        ["0", "1", "3"],
        ["2", "1", "8"],
        ["4", "2", "13"],
    ]
    actual = read_file(file_obj, "txt", ",")
    assert expected == actual


def test_read_file_tsv():
    file_obj = StringIO(
        "x\ty\tz\n"
        "0\t1\t3\n"
        "2\t1\t8\n"
        "4\t2\t13\n"
    )
    expected = [
        ["x", "y", "z"],
        ["0", "1", "3"],
        ["2", "1", "8"],
        ["4", "2", "13"],
    ]
    actual = read_file(file_obj, "tsv", None)
    assert expected == actual


def test_read_file_tsv_specified_sep():
    file_obj = StringIO(
        "x\ty\tz\n"
        "0\t1\t3\n"
        "2\t1\t8\n"
        "4\t2\t13\n"
    )
    expected = [
        ["x", "y", "z"],
        ["0", "1", "3"],
        ["2", "1", "8"],
        ["4", "2", "13"],
    ]
    actual = read_file(file_obj, "tsv", "\t")
    assert expected == actual


def test_read_file_csv_file_type_error():
    file_obj = StringIO(
        "x,y,z\n"
        "0,1,3\n"
        "2,1,8\n"
        "4,2,13\n"
    )
    with pytest.raises(ValueError) as e:
        _ = read_file(file_obj, "txt", None)
    assert str(e.value) == "Failed to estimate separator character. Please specify sep explicitly."


@pytest.mark.parametrize(
    ("str_cells", "next_id", "expected"),
    [
        (
                # single column, no label
                [["42.1"], ["42.2"]],
                0,
                [DataSequence([0, 1], [42.1, 42.2], 0, None)]
        ),
        (
                # single column, label specified
                [["value"], ["42.1"], ["42.2"]],
                0,
                [DataSequence([0, 1], [42.1, 42.2], 0, "value")]
        ),
        (
                # double column, no label
                [["0.5", "42.1"], ["1.5", "42.2"]],
                0,
                [DataSequence([0.5, 1.5], [42.1, 42.2], 0, None)]
        ),
        (
                # double column, label specified
                [["x", "y"], ["0.5", "42.1"], ["1.5", "42.2"]],
                0,
                [DataSequence([0.5, 1.5], [42.1, 42.2], 0, "y")]
        ),
        (
                # triple column, no label
                [["0.5", "42.1", "100.4"], ["1.5", "42.2", "103.5"]],
                0,
                [DataSequence([0.5, 1.5], [42.1, 42.2], 0, None), DataSequence([0.5, 1.5], [100.4, 103.5], 1, None)]
        ),
        (
                # triple column, label specified
                [["x", "y1", "y2"], ["0.5", "42.1", "100.4"], ["1.5", "42.2", "103.5"]],
                0,
                [DataSequence([0.5, 1.5], [42.1, 42.2], 0, "y1"), DataSequence([0.5, 1.5], [100.4, 103.5], 1, "y2")]
        ),
        (
                # triple column, label specified, next_id shifted
                [["x", "y1", "y2"], ["0.5", "42.1", "100.4"], ["1.5", "42.2", "103.5"]],
                5,
                [DataSequence([0.5, 1.5], [42.1, 42.2], 5, "y1"), DataSequence([0.5, 1.5], [100.4, 103.5], 6, "y2")]
        ),
    ]
)
def test_parse(str_cells: list[list[str]], next_id: int, expected: list[DataSequence]):
    actual = parse(str_cells, next_id)
    assert actual == expected


def test_parse_not_aligned_error():
    str_cells = [
        ["x", "y"],
        ["0", "1"],
        ["1"],
    ]
    with pytest.raises(ValueError) as e:
        _ = parse(str_cells, 0)
    assert str(e.value) == "The length of column is not aligned."


def test_parse_type_error():
    str_cells = [
        ["x", "y"],
        ["0", "1"],
        ["1", "A"],
    ]
    with pytest.raises(TypeError) as e:
        _ = parse(str_cells, 0)
    assert str(e.value) == "int or float type are only available."
