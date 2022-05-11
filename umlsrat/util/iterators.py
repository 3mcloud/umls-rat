from typing import Iterable, Iterator


def yield_unique(gen: Iterator, seen: Iterable = None):
    if seen:
        seen = set(seen)
    else:
        seen = set()

    for e in gen:
        if e not in seen:
            yield e
        seen.add(e)
