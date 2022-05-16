from typing import Iterable, List

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import umls


def map_cuis_to_names(api: MetaThesaurus, cuis: Iterable[str]) -> List[str]:
    return [umls.get_concept_name(api, cui) for cui in cuis]
