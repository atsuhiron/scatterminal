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
