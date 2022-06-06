from typing import Iterable, List

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import lookup_umls


def map_cuis_to_names(api: MetaThesaurus, cuis: Iterable[str]) -> List[str]:
    return [lookup_umls.get_concept_name(api, cui) for cui in cuis]
