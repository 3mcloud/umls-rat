import collections
import logging
import os.path
import re
from typing import Optional, Dict, List, Iterable

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util import misc

logger = logging.getLogger(os.path.basename(__file__))


def _get_umls_concept(api: MetaThesaurus, result: Dict) -> Optional[Dict]:
    for c_uri in (result[_] for _ in ("concept", "concepts") if _ in result):
        concept_res = api.get_results(c_uri)
        if not concept_res:
            continue
        for c in concept_res:
            # check for valid UI
            if c["ui"]:
                return c


def _find_umls(api: MetaThesaurus, source_res: Dict) -> Dict:
    umls = _get_umls_concept(api, source_res)
    if umls:
        return umls

    # if we didn't find a UMLS concept directly, check 'SY' then 'RO' relations
    relations = api.get_results(source_res.get("relations"))
    grouped = misc.group_data(relations, lambda _: _["relationLabel"])

    for rel_type in (
        "SY",
        "RO",
    ):
        rels = grouped.get(rel_type)
        if not rels:
            logger.info(f"'{source_res['ui']}' has no '{rel_type}' relations")
            continue

        for rel in rels:
            rel_concept = api.get_single_result(rel["relatedId"])
            return _get_umls_concept(api, rel_concept)

    raise ValueError(f"Impossible to find UMLS concept for:\n{source_res}")


def find_umls(api: MetaThesaurus, source_vocab: str, concept_id: str) -> Optional[str]:
    """
    Get the UMLS CUI for a concept from a source vocabulary.

    :param api: MetaThesaurus API
    :param source_vocab: source vocabulary abbrev (i.e. SNOMEDCT_US)
    :param concept_id: source concept ID
    :return: UMLS CUI or None
    """
    source_res = api.get_source_concept(source_vocab, concept_id)
    if not source_res:
        logger.info(f"Concept not found: {source_vocab}/{concept_id}")
        return None

    concept_res = _find_umls(api, source_res)
    return concept_res["ui"]


def _term_search(api: MetaThesaurus, term: str) -> Optional[Dict]:
    for st in ("words", "normalizedWords", "approximate"):
        for it in (
            "sourceConcept",
            "sourceDescriptor",
        ):
            search_params = dict(inputType=it, searchType=st)
            concepts = api.search(term, **search_params)
            # filter bogus results
            concepts = [_ for _ in concepts if _["ui"]]
            if concepts:
                return dict(**search_params, concepts=concepts)
    return None


def term_search(api: MetaThesaurus, term: str) -> Optional[Dict]:
    # remove trailing parentheses e.g. Room air (substance)
    normalized = re.sub(r"\s*\(.+?\)\s*$", "", term)
    return _term_search(api, normalized)


def get_semantic_types(api: MetaThesaurus, cui: str) -> List[Dict]:
    concept = api.get_concept(cui)
    if not concept:
        raise ValueError(f"No such concept '{cui}")

    semantic_types = concept.get("semanticTypes")
    if not semantic_types:
        return []

    return [
        {
            "name": stype["name"],
            "definition": api.get_single_result(stype["uri"]).get("definition"),
        }
        for stype in semantic_types
    ]


def get_broader_concepts(api: MetaThesaurus, cui: str) -> Iterable[str]:
    allowed_relations = ("SY", "RN", "CHD")

    related_concepts = api.get_related_concepts(
        cui, relationLabels=",".join(allowed_relations)
    )

    # group by relation type
    grouped = collections.defaultdict(list)
    for rc in related_concepts:
        grouped[rc["label"]].append(rc["concept"])

    seen = set()
    for rtype in allowed_relations:
        for cui in grouped[rtype]:
            if cui not in seen:
                seen.add(cui)
                yield cui
