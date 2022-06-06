from typing import Iterable, List, Dict

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import lookup_umls


def map_cuis_to_names(api: MetaThesaurus, cuis: Iterable[str]) -> List[str]:
    return [lookup_umls.get_concept_name(api, cui) for cui in cuis]


def extract_concept_names(concepts: List[Dict]) -> List[str]:
    return [_["name"] for _ in concepts]


def extract_definitions(concepts: List[Dict]) -> List[str]:
    defs = []
    for concept in concepts:
        for d in concept["definitions"]:
            defs.append(d)
    return [d["value"] for d in defs]
