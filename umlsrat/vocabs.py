""" Incomplete representation of this:
https://www.nlm.nih.gov/research/umls/sourcereleasedocs/index.html
"""

_VOCABULARIES = {
    'SNOMEDCT_US': {
        'SNOMED', 'SNOMEDCT'
    },
    'MSH': {
        'MESH'
    },
    'RXNORM': {
    }
}


def find_vocab_abbr(name: str) -> str:
    norm = name.strip().upper()
    if norm in _VOCABULARIES:
        return norm

    for name, alternates in _VOCABULARIES.items():
        if norm in alternates:
            return name

    raise ValueError(f"Could not find vocab abbrev for: {name}")
