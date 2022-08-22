import re
from typing import List, Callable, Iterable

_ENCLOSING_CITATION = {")": "(", "]": "[", ">": "<"}


def remove_trailing_parens(text: str) -> str:
    # remove trailing parentheses e.g. "Room air (substance)" or "foo bar (klopfer: 2022)"
    close_char = text[-1]
    if close_char in _ENCLOSING_CITATION:
        stack = [close_char]
        open_char = _ENCLOSING_CITATION.get(close_char)
        i = len(text) - 2
        while i >= 0:
            cur_char = text[i]
            if cur_char == open_char:
                stack.pop()
                if not stack:
                    break
            elif cur_char == close_char:
                stack.append(close_char)

            i -= 1
        if i > 0:
            return text[:i]

    return text


def clean_definition_text(text: str) -> str:
    clean = text.strip()
    if not clean:
        return clean
    # clean trailing citation
    clean = remove_trailing_parens(clean)
    # xml tags
    clean = re.sub(r"<[^<]+?>", "", clean)

    return clean.strip()


_NOS_PAT = re.compile(r",?\s*NOS$")
_PUNCT_PAT = re.compile(r"\s*[,;:?_{|}.=()\[\]!/<>\"\\~-]\s*")


def normalize(text_str: str) -> str:
    """Normalize string"""
    # remove NOS (SNOMED ; Not Otherwise Specified)
    normalized = _NOS_PAT.sub("", text_str)
    normalized = clean_definition_text(normalized.lower())
    normalized = _PUNCT_PAT.sub(" ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


_STOP_WORDS = {"of", "the", "by"}


def tokenize(text_str: str) -> List[str]:
    """Tokenize string"""
    return [_ for _ in text_str.split() if _ and _ not in _STOP_WORDS]


def norm_tokenize(text_str: str) -> List[str]:
    """Normalize string, then tokenize"""
    return tokenize(normalize(text_str))


def _hammingish(source: Iterable[str], target: Iterable[str]) -> float:
    """This distance metric favors shorter 'target' sequences"""
    ss, st = set(source), set(target)

    dist = len(st - ss) / len(st)
    return dist


def hammingish(source: List[str], target: List[str]) -> float:
    return max(_hammingish(source, target), _hammingish(target, source))


def hammingish_str(source: str, target: str) -> float:
    return hammingish(norm_tokenize(source), norm_tokenize(target))


def hammingish_partial(source_txt: str) -> Callable[[str], float]:
    source = norm_tokenize(source_txt)

    def sort_key(target_txt: str) -> float:
        target = norm_tokenize(target_txt)
        return hammingish(source, target)

    return sort_key


def identity(text: str) -> str:
    return text
