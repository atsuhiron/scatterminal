import math


def log(value: float | int) -> float:
    return math.log10(value)


def exp(value: float | int) -> float:
    return 10.0 ** value


def abs_to_rel(value: int | float, range_: int | float, min_: int | float) -> float:
    return (value - min_) / range_
