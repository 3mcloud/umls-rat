import csv
from collections import namedtuple, OrderedDict
from typing import Tuple, Iterable, Iterator, Any, ItemsView, ValuesView, KeysView


def _norm_field_name(field_name: Any) -> str:
    return str(field_name).replace(" ", "")


class SimpleTable(object):
    """
    A list of rows with a single index field.
    """

    def __init__(self, all_rows: Iterator[Iterable], index_field: str):
        super(SimpleTable, self).__init__()
        self._index_field = index_field
        self._data = OrderedDict()

        # first row is the header
        header = next(all_rows)
        # make them valid field names
        self._field_names = tuple(_norm_field_name(_) for _ in header)
        assert index_field in self._field_names
        row_type = namedtuple("RowType", self._field_names)

        for row in all_rows:
            datum = row_type(*row)
            idx_val = getattr(datum, index_field)
            incumbent = self._data.get(idx_val)
            assert not incumbent, (
                f"Value already exists for index {idx_val}:\n" f"{incumbent}"
            )
            self._data[idx_val] = datum

    def get(self, index_val):
        return self._data.get(index_val)

    def items(self) -> ItemsView:
        return self._data.items()

    def values(self) -> ValuesView:
        return self._data.values()

    def keys(self) -> KeysView:
        return self._data.keys()

    @staticmethod
    def load_csv(csv_path: str, index_field: str) -> "SimpleTable":
        with open(csv_path, "r", encoding="utf8") as fp:
            reader = csv.reader(fp)
            return SimpleTable(reader, index_field)

    @property
    def index_field(self) -> str:
        return self._index_field

    @property
    def fields(self) -> Tuple[str, ...]:
        return self._field_names
