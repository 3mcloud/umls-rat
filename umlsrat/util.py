import itertools
from typing import Callable, Any, Dict, List, Iterable


def group_data(data: Iterable, key_fn: Callable[[Any], Any]) -> Dict[Any, List]:
    grouped = dict()
    data = sorted(data, key=key_fn)
    for k, g in itertools.groupby(data, key_fn):
        grouped[k] = list(g)  # Store group iterator as a list

    return grouped
