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


def norm_tokenize(text_str: str) -> List[str]:
    normalized = text_str.lower().replace(string.punctuation, "")
    return [_ for _ in normalized.split() if _]
