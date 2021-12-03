import logging
import os.path
from typing import Optional, Iterable

logger = logging.getLogger(os.path.basename(__file__))


class UniqueFIFO(object):
    def __init__(self, iterable: Optional[Iterable] = None):
        self._uniq = set()
        self._list = list()
        if iterable:
            self.push_all(iterable)

    def push(self, item):
        if item not in self._uniq:
            self._list.append(item)
            self._uniq.add(item)

    def pop(self):
        item = self._list.pop(0)
        self._uniq.discard(item)
        return item

    def peek(self):
        return self._list[0]

    def push_all(self, iterable):
        for item in iterable:
            self.push(item)

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __contains__(self, item):
        return item in self._uniq

    def __str__(self):
        return str(self._list)

    def __repr__(self):
        return str(self)
