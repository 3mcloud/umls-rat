import itertools
import re
from typing import Callable, Any, Dict, Iterable
from typing import List


def strip_tags(text: str) -> str:
    return re.sub(r'<[^<]+?>', '', text.strip())


def group_data(data: Iterable, key_fn: Callable[[Any], Any]) -> Dict[Any, List]:
    """https://docs.python.org/3/library/itertools.html#itertools.groupby"""
    grouped = dict()
    data = sorted(data, key=key_fn)
    for k, g in itertools.groupby(data, key_fn):
        grouped[k] = list(g)  # Store group iterator as a list

    return grouped
