import re
import string
from typing import List


def clean_definition_text(text: str) -> str:
    # xml tags
    clean = re.sub(r"<[^<]+?>", "", text)
    # random trailing abbrevs
    clean = re.sub(r"\s*\([A-Z]{3}\)\s*$", "", clean)
    # trailing []
    clean = re.sub(r"\[\]", "", clean)
    return clean.strip()


_RM_PUNCT_PAT = re.compile(rf"[{string.punctuation}]")


def normalize(text_str: str) -> str:
    """Normalize string"""
    normalized = text_str.lower()
    normalized = _RM_PUNCT_PAT.sub(" ", normalized)
    return normalized


_STOP_WORDS = {"of", "the", "by"}


def tokenize(text_str: str) -> List[str]:
    """Tokenize string"""
    return [_ for _ in text_str.split() if _ and _ not in _STOP_WORDS]


def norm_tokenize(text_str: str) -> List[str]:
    """Normalize string, then tokenize"""
    return tokenize(normalize(text_str))


def hammingish(source: List[str], target: List[str]) -> float:
    """This distance metric favors shorter 'target' sequences"""
    ss, st = set(source), set(target)

    return len(st - ss) / len(st)
