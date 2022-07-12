import textwrap
from itertools import cycle, islice
from typing import List, Dict


def _entry_to_string(name: str, definitions: List[Dict]) -> str:
    value = ""
    value += f"{name}\n"
    value += "=" * len(name)
    value += "\n"
    enum_defs = (
        textwrap.fill(f"{x + 1}. {datum['value']}")
        for x, datum in enumerate(definitions)
    )
    value += "\n".join(enum_defs)
    return value


def definitions_to_md(concepts: List[Dict]) -> str:
    """
    Write list of defined concepts as MarkDown.

    :param concepts: list of concept Dicts
    :return: MarkDown string
    """
    entries = (_entry_to_string(c["name"], c["definitions"]) for c in concepts)
    return "\n\n".join(entries)


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
