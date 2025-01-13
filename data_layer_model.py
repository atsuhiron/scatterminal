import dataclasses
from enum import Enum
import warnings


@dataclasses.dataclass(frozen=True)
class DataSequence:
    x: list[int | float]
    y: list[int | float]
    _id: int
    name: str | None = None

    def __post_init__(self):
        if len(self.x) != len(self.y):
            raise ValueError("length of x and y must be equal: (index={0}, len(x)={1}, len(y)={2})".format(self._id, len(self.x), len(self.y)))
        if not all(map(lambda x: isinstance(x, (int, float)), self.x)):
            raise ValueError("x must be list[int | float]: index={0}".format(self._id))
        if not all(map(lambda y: isinstance(y, (int, float)), self.y)):
            raise ValueError("y must be list[int | float: index={0}".format(self._id))
        if (self.name is not None) and (not self.name.isascii()):
            raise ValueError("Sequence name must be ascii: index={0}".format(self._id))


class DataScaleType(str, Enum):
    linear = "linear"
    log = "log"


@dataclasses.dataclass(frozen=True)
class DataAxis:
    scale: DataScaleType = DataScaleType.linear
    name: str | None = None
    min_: int | float | None = None
    max_: int | float | None = None

    def __post_init__(self):
        if (self.name is not None) and (not self.name.isascii()):
            raise ValueError("Axis name must be ascii")
        if (self.min_ is None) != (self.max_ is None):
            raise ValueError("Axis min and Axis max should be defined simultaneously")


@dataclasses.dataclass(frozen=True)
class Data:
    data: list[DataSequence]
    x_axis: DataAxis
    y_axis: DataAxis

    def __post_init__(self):
        if self.x_axis.scale == DataScaleType.log:
            for datum in self.data:
                if min(datum.x) <= 0:
                    warnings.warn("Non-positive value is detected on log-scale. This data point is not plotted.")
        if self.y_axis.scale == DataScaleType.log:
            for datum in self.data:
                if min(datum.y) <= 0:
                    warnings.warn("Non-positive value is detected on log-scale. This data point is not plotted.")
        