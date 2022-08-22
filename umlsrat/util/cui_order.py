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


def cui_name_sim(api: MetaThesaurus, source_cui: str) -> Callable[[str], Any]:
    source_name = api.get_concept(source_cui).get("name")
    if source_name is None:
        mth_atom = list(api.get_atoms_for_cui(source_cui, sabs="MTH")).pop()
        source_name = mth_atom.get("name")
    assert source_name, f"No name for CUI {source_cui}"
    return desc_name_sim(api, source_name)


def desc_name_sim(api: MetaThesaurus, desc: str) -> Callable[[str], Any]:
    hammingish = text.hammingish_partial(desc)

    def sort_fn(cui: str):
        concept = api.get_concept(cui)
        target = concept.get("name")
        return hammingish(target), target

    return sort_fn


def relation_count(api: MetaThesaurus, dsc: bool = False) -> Callable[[str], int]:
    def sort_fn(cui: str) -> int:
        cnt = api.get_concept(cui).get("relationCount")
        return -cnt if dsc else cnt

    return sort_fn
