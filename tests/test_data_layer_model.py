from typing import Callable

import pytest

import scatterminal.data_layer_model as dlm


@pytest.mark.parametrize(
    ("filter_func", "data_seq", "expected"),
    [
        # positive-pass filter x
        (
            lambda xy: xy[0] > 0,
            dlm.DataSequence(
                x=[1, 2, 3],
                y=[1, 2, 3],
                seq_id=0
            ),
            dlm.DataSequence(
                x=[1, 2, 3],
                y=[1, 2, 3],
                seq_id=0
            )
        ),
        (
            lambda xy: xy[0] > 0,
            dlm.DataSequence(
                x=[1, -2, 3],
                y=[1, 2, 3],
                seq_id=0
            ),
            dlm.DataSequence(
                x=[1, 3],
                y=[1, 3],
                seq_id=0
            )
        ),
        (
            lambda xy: xy[0] > 0,
            dlm.DataSequence(
                x=[1, 2, 3],
                y=[1, -2, 3],
                seq_id=0
            ),
            dlm.DataSequence(
                x=[1, 2, 3],
                y=[1, -2, 3],
                seq_id=0
            )
        ),

        # positive-pass filter y
        (
            lambda xy: xy[1] > 0,
            dlm.DataSequence(
                x=[1, 2, 3],
                y=[1, 2, 3],
                seq_id=0
            ),
            dlm.DataSequence(
                x=[1, 2, 3],
                y=[1, 2, 3],
                seq_id=0
            )
        ),
        (
            lambda xy: xy[1] > 0,
            dlm.DataSequence(
                x=[1, -2, 3],
                y=[1, 2, 3],
                seq_id=0
            ),
            dlm.DataSequence(
                x=[1, -2, 3],
                y=[1, 2, 3],
                seq_id=0
            )
        ),
        (
            lambda xy: xy[1] > 0,
            dlm.DataSequence(
                x=[1, 2, 3],
                y=[1, -2, 3],
                seq_id=0
            ),
            dlm.DataSequence(
                x=[1, 3],
                y=[1, 3],
                seq_id=0
            )
        )
    ]
)
def test_data_sequence_create_filtered(
        filter_func: Callable[[tuple[int | float, int | float]], bool],
        data_seq: dlm.DataSequence,
        expected: dlm.DataSequence
):
    actual = data_seq.create_filtered(filter_func)
    assert actual == expected


@pytest.mark.parametrize(
    ("x", "y", "seq_id", "name", "x_name", "error_type", "expected"),
    [
        ([0], [1, 2], 9, None, None, ValueError, "length of x and y must be equal: (seq_id=9, len(x)=1, len(y)=2)"),
        ([0, "A"], [1, 2], 9, None, None, TypeError, "x must be list[int | float]: seq_id=9"),
        ([0, 1], [1, "A"], 9, None, None, TypeError, "y must be list[int | float]: seq_id=9"),
        ([0, 1], [1, 2], 9, "あ", None, ValueError, "Sequence name must be ascii: seq_id=9"),
        ([0, 1], [1, 2], 9, None, "あ", ValueError, "Sequence x_name must be ascii: seq_id=9")
    ]
)
def test_data_sequence_error(
        x: list[int | str], y: list[int | str],
        seq_id, name: str | None, x_name: str | None,
        error_type: type[Exception], expected: str
):
    with pytest.raises(error_type) as e:
        _ = dlm.DataSequence(x, y, seq_id, name, x_name)
    assert str(e.value) == expected


@pytest.mark.parametrize(
    ("scale", "name", "min_", "max_", "expected"),
    [
        (dlm.DataScaleType.linear, "あ", 0, 1, "Axis name must be ascii: あ"),
        (dlm.DataScaleType.linear, "a", 0, None, "Axis min and Axis max should be defined simultaneously: (min, max)=(0, None)"),
        (dlm.DataScaleType.linear, "a", None, 0, "Axis min and Axis max should be defined simultaneously: (min, max)=(None, 0)"),
        (dlm.DataScaleType.linear, "a", 0, 0, "Axis min is larger than max: (min, max)="),
        (dlm.DataScaleType.log, "a", 0, 10, "Axis min must be positive value on log-scale"),
    ]
)
def test_data_axis_error(scale: dlm.DataScaleType, name: str | None, min_: int | None, max_: int | None, expected: str):
    with pytest.raises(ValueError) as e:
        _ = dlm.DataAxis(scale, name, min_, max_)
    assert expected in str(e.value)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            [dlm.DataSequence([0, 1], [1, 2], 9)],
            "Non-positive value is detected on log-scale x axis. This data point is not plotted.: seq_id=9"
        ),
        (
            [dlm.DataSequence([1, 1], [0, 2], 9)],
            "Non-positive value is detected on log-scale y axis. This data point is not plotted.: seq_id=9"
        )
    ]
)
def test_data_warning(data: list[dlm.DataSequence], expected: str):
    with pytest.warns(UserWarning) as e:
        _ = dlm.Data(data, dlm.DataAxis(dlm.DataScaleType.log), dlm.DataAxis(dlm.DataScaleType.log), dlm.DataLegendLoc.lower)
    assert str(e.list[0].message) == expected
