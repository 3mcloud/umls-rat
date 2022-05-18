from itertools import cycle, islice
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


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))
