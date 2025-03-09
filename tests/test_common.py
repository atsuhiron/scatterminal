import pytest

import scatterminal.common as common


@pytest.mark.parametrize(
    ("value", "range_", "min_", "expected"),
    [
        (5, 10, 0, 0.5),
        (15, 10, 10, 0.5),
    ]
)
def test_abs_to_rel(value: int | float, range_: int | float, min_: int | float, expected: float):
    assert common.abs_to_rel(value, range_, min_) == expected


@pytest.mark.parametrize(
    ("value",),
    [
        (1,),
        (1.0,),
        (180.5,)
    ]
)
def test_log_exp(value: int | float):
    assert common.exp(common.log(value)) == pytest.approx(float(value))
