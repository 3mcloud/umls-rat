from typing import Callable

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util import text


def cui_by_concept_name_dist(
    api: MetaThesaurus, source_cui: str
) -> Callable[[str], float]:
    source = api.get_concept(source_cui).get("name")
    fn = text.hammingish_partial(source)

    def sort_fn(cui: str) -> float:
        target = api.get_concept(cui).get("name")
        return fn(target)

    return sort_fn
