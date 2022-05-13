from typing import Callable, Tuple, Dict, Set, Any

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util import text


def _get_sem_types(concept: Dict) -> Set[str]:
    return {_.get("name") for _ in concept.get("semanticTypes")}


def sem_type_name_sim(
    api: MetaThesaurus, source_cui: str
) -> Callable[[str], Tuple[bool, float]]:
    source = api.get_concept(source_cui)
    source_sem_types = _get_sem_types(source)
    hammingish = text.hammingish_partial(source.get("name"))

    def sort_fn(cui: str) -> Tuple[bool, float]:
        target = api.get_concept(cui)
        target_sem_types = _get_sem_types(target)
        overlap = bool(source_sem_types & target_sem_types)
        return not overlap, hammingish(target.get("name"))

    return sort_fn


def name_sim(api: MetaThesaurus, source_cui: str) -> Callable[[str], float]:
    source = api.get_concept(source_cui).get("name")
    hammingish = text.hammingish_partial(source)

    def sort_fn(cui: str) -> float:
        target = api.get_concept(cui).get("name")
        return hammingish(target)

    return sort_fn


def cui_distance(api: MetaThesaurus, source_cui: str) -> Callable[[str], Any]:
    return name_sim(api, source_cui)
