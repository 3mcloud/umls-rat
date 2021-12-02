""" Incomplete representation of this:
https://www.nlm.nih.gov/research/umls/sourcereleasedocs/index.html
"""
import csv
import functools
import os
from collections import namedtuple, OrderedDict
from typing import NamedTuple, Optional, Tuple

_THIS_DIR = os.path.dirname(os.path.normpath(__file__))
_VOCABULARIES_CSV = os.path.join(_THIS_DIR, 'vocabularies.csv')


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


@functools.lru_cache(maxsize=1)
def VOCAB_INFO() -> ShittyDF:
    return ShittyDF(_VOCABULARIES_CSV, 'Abbreviation')


def get_vocab_info(abbrev: str) -> Optional[NamedTuple]:
    norm = abbrev.strip().upper()
    voc_info = VOCAB_INFO()
    return voc_info.get(norm)


def validate_abbrev(abbrev: str):
    info = get_vocab_info(abbrev)
    if not info:
        message = "Unknown vocabulary abbreviation: '{}'. Try one of these: {}".format(
            abbrev, "\n".join(str(_) for _ in VOCAB_INFO().values())
        )
        raise ValueError(message)
