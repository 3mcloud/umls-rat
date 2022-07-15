import textwrap
from itertools import cycle, islice
from typing import List, Dict, Iterable

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import lookup_umls


def map_cuis_to_names(api: MetaThesaurus, cuis: Iterable[str]) -> List[str]:
    """
    Map CUIs to concept names.
    :param api: meta thesaurus object
    :param cuis: CUIs
    :return: names
    """
    return [lookup_umls.get_concept_name(api, cui) for cui in cuis]


def extract_concept_names(concepts: List[Dict]) -> List[str]:
    """
    Extract names from concepts.
    :param concepts: concept dicts
    :return: names
    """
    return [_["name"] for _ in concepts]


def extract_definitions(concepts: List[Dict]) -> List[str]:
    """
    Extract definition text from concepts.
    :param concepts: concept dicts
    :return: definitions
    """
    defs = []
    for concept in concepts:
        for d in concept["definitions"]:
            defs.append(d)
    return [d["value"] for d in defs]


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
