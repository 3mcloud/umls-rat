import csv
import itertools
import re
from collections import namedtuple, OrderedDict
from typing import Callable, Any, Dict, Iterable
from typing import Tuple, List


def strip_tags(text: str) -> str:
    return re.sub(r'<[^<]+?>', '', text)


def group_data(data: Iterable, key_fn: Callable[[Any], Any]) -> Dict[Any, List]:
    """https://docs.python.org/3/library/itertools.html#itertools.groupby"""
    grouped = dict()
    data = sorted(data, key=key_fn)
    for k, g in itertools.groupby(data, key_fn):
        grouped[k] = list(g)  # Store group iterator as a list

    return grouped


def _norm_field_name(field_name: str):
    return field_name.replace(' ', '')


class ShittyDF(OrderedDict):
    def __init__(self, csv_path: str, index: str):
        super(ShittyDF, self).__init__()
        self._index_name = index
        with open(csv_path, 'r', encoding='utf8') as fp:
            reader = csv.reader(fp)
            first_row = next(reader)
            # make them valid field names
            self._field_names = tuple(_norm_field_name(_) for _ in first_row)
            assert index in self._field_names
            row_type = namedtuple('RowType', self._field_names)
            for row in reader:
                datum = row_type(*row)
                idx_val = getattr(datum, index)
                incumbent = self.get(idx_val)
                assert not incumbent, \
                    f"Value already exists for index {idx_val}:\n{incumbent}"
                self[idx_val] = datum

    @property
    def index_field(self) -> str:
        return self._index_name

    @property
    def fields(self) -> Tuple[str, ...]:
        return self._field_names
