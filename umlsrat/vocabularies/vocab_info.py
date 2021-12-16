"""
See: https://www.nlm.nih.gov/research/umls/sourcereleasedocs/index.html
"""
import functools
import os
from collections import Counter
from typing import NamedTuple, Optional, List

from umlsrat.util.simple_table import SimpleTable

_THIS_DIR = os.path.dirname(os.path.normpath(__file__))
_VOCABULARIES_CSV = os.path.join(_THIS_DIR, "vocabularies.csv")

# Mapping from MModal Terminology CodeSystem names to Metathesaurus names
_MM_CODE_SYS_MAP = {"SNOMED-CT": "SNOMEDCT_US", "SNOMED": "SNOMEDCT_US"}


@functools.lru_cache(maxsize=1)
def _get_vocab_table() -> SimpleTable:
    return SimpleTable.load_csv(csv_path=_VOCABULARIES_CSV, index_field="Abbreviation")


def _normalize_abbrev(abbrev: str) -> str:
    norm = abbrev.strip().upper()
    return _MM_CODE_SYS_MAP.get(norm, norm)


def get_vocab_info(abbrev: str) -> Optional[NamedTuple]:
    """
    Get vocab info for a vocabulary abbreviation or name
    :param abbrev: vocab abbreviation or name
    :return: vocab info
    """
    norm = _normalize_abbrev(abbrev)
    voc_info = _get_vocab_table()
    return voc_info.get(norm)


def validate_vocab_abbrev(abbrev: str) -> str:
    """
    Look up the vocab name or abbreviation and return the properly normalized one.
    :param abbrev: vocab abbreviation or name
    :return: proper vocab abbreviation
    """
    info = get_vocab_info(abbrev)
    if not info:
        message = "Unknown vocabulary abbreviation: '{}'. Try one of these:\n{}".format(
            abbrev, "\n".join(str(_) for _ in _get_vocab_table().values())
        )
        raise ValueError(message)
    return info.Abbreviation


@functools.lru_cache(maxsize=2)
def vocabs_for_language(lang: str) -> List[str]:
    """
    Get a list of vocabularies for a given language abbrev
    :param lang: language abbreviation
    :return: list of vocabulary abbreviations
    """
    return [
        info.Abbreviation
        for info in _get_vocab_table().values()
        if info.Language == lang
    ]


def available_vocabs() -> List[str]:
    """
    All available vocabulary abbreviations
    :return: list of vocabulary abbreviations
    """
    table = _get_vocab_table()
    return list(table.keys())


@functools.lru_cache(maxsize=1)
def available_languages() -> List[str]:
    """
    All available language abbreviations.
    :return: list of language abbreviations
    """
    table = _get_vocab_table()
    cnt = Counter(info.Language for info in table.values() if info.Language)
    return [abbrev for abbrev, _ in cnt.most_common()]
