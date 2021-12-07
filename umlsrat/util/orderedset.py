import logging
import os.path
from typing import Optional, Iterable, Callable, Any

logger = logging.getLogger(os.path.basename(__file__))


class FIFO(object):
    def __init__(self,
                 iterable: Optional[Iterable] = None, ):
        if iterable:
            self._list = list(iterable)
        else:
            self._list = list()

    def push(self, item):
        self._list.append(item)

    def pop(self):
        item = self._list.pop(0)
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
        return item in self._list

    def __str__(self):
        return str(self._list)

    def __repr__(self):
        return str(self)


class UniqueFIFO(object):
    def __init__(self,
                 iterable: Optional[Iterable] = None,
                 keyfn: Optional[Callable[[Any], Any]] = None):
        self._uniq = set()
        self._list = list()
        if keyfn:
            self._keyfn = keyfn
        else:
            self._keyfn = lambda _: _

        if iterable:
            self.push_all(iterable)

    def push(self, item):
        key = self._keyfn(item)
        if key not in self._uniq:
            self._list.append(item)
            self._uniq.add(key)

    def pop(self):
        item = self._list.pop(0)
        self._uniq.discard(self._keyfn(item))
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
        return self._keyfn(item) in self._uniq

    def __str__(self):
        return str(self._list)

    def __repr__(self):
        return str(self)