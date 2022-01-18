import logging
import os.path
import re
import string
from typing import Optional, Dict, List, Set, Iterator

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util import misc, orderedset
from umlsrat.vocabularies import vocab_info
from umlsrat.vocabularies.vocab_info import validate_vocab_abbrev

logger = logging.getLogger(os.path.basename(__file__))


def _get_umls_concept(api: MetaThesaurus, result: Dict) -> Optional[Dict]:
    for c_uri in (result[_] for _ in ("concept", "concepts") if _ in result):
        concept_res = api.get_results(c_uri)
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


def _term_search(api: MetaThesaurus, term: str, max_results: int) -> Dict:
    for st in ("words", "normalizedWords", "approximate"):
        for it in (
            "sourceConcept",
            "sourceDescriptor",
        ):
            search_params = dict(
                inputType=it, searchType=st, pageSize=min(25, max_results)
            )
            concepts = api.search(term, max_results=max_results, **search_params)
            # filter bogus results
            concepts = [_ for _ in concepts if _["ui"]]
            if concepts:
                return dict(**search_params, searchTerm=term, concepts=concepts)

    return dict(searchTerm=term, concepts=[])


def _normalize_for_match(text: str):
    return re.sub(rf"[{string.punctuation}]+", " ", text.lower())


def _is_strict_match(original: str, matched: str) -> bool:
    original = _normalize_for_match(original)
    matched = _normalize_for_match(matched)

    return original in matched


def term_search(
    api: MetaThesaurus,
    term: str,
    max_results: Optional[int] = 1000,
    strict_match: Optional[bool] = False,
) -> Dict:
    # remove trailing parentheses e.g. Room air (substance)
    normalized = re.sub(r"\s*\(.+?\)\s*$", "", term)
    result = _term_search(api, normalized, max_results)

    if strict_match:
        result["concepts"] = [
            concept
            for concept in result["concepts"]
            if _is_strict_match(result["searchTerm"], concept["name"])
        ]

    return result


def get_semantic_types(api: MetaThesaurus, cui: str) -> List[Dict]:
    """
    Get semantic type info associated with this concept. Resulting type information takes the form,
    {
        "name": name of semantic type,
        "info": extended information about that type
    }
    :param api: meta thesaurus
    :param cui: target concept
    :return: list of semantic type information objects
    """
    concept = api.get_concept(cui)
    if not concept:
        raise ValueError(f"No such concept '{cui}")

    semantic_types = concept.get("semanticTypes")
    if not semantic_types:
        return []

    return [
        {
            "name": stype["name"],
            "data": api.get_single_result(stype["uri"]),
        }
        for stype in semantic_types
    ]


def get_semantic_type_groups(api: MetaThesaurus, cui: str) -> Set[str]:
    """Convenience function to get the set of semantic type *group* names for a concept"""
    sem_types = get_semantic_types(api, cui)
    return {_["data"]["semanticTypeGroup"]["expandedForm"] for _ in sem_types}


def get_semantic_type_names(api: MetaThesaurus, cui: str) -> Set[str]:
    """Convenience function to get the set of semantic type names for a concept"""
    sem_types = get_semantic_types(api, cui)
    return {_["name"] for _ in sem_types}


def _do_cui_search(
    api: MetaThesaurus, source_vocab: str, concept_id: str
) -> Optional[str]:
    search_params = dict(
        inputType="sourceUi",
        searchType="exact",
        # includeObsolete=True,
        # includeSuppressible=True,
        sabs=source_vocab,
    )
    results = list(api.search(string=concept_id, max_results=1, **search_params))
    if results:
        return results[0]["ui"]

    return None


def get_cui_for(
    api: MetaThesaurus, source_vocab: str, concept_id: str
) -> Optional[str]:
    """
    Get UMLS CUI for a source concept.
    /search/current?string=9468002&inputType=sourceUi&searchType=exact&sabs=SNOMEDCT_US

    :param api:
    :param source_vocab:
    :param concept_id:
    :return: CUI or None if not found
    """

    assert concept_id
    source_vocab = validate_vocab_abbrev(source_vocab)

    cui = _do_cui_search(api, source_vocab, concept_id)
    if cui:
        return cui

    ## might have an obsolete concept
    def get_related(label: str):
        return [
            api.get_single_result(rel["relatedId"])
            for rel in api.get_source_relations(
                source_vocab=source_vocab,
                concept_id=concept_id,
                includeRelationLabels=label,
            )
        ]

    # check synonyms
    for related_concept in get_related("SY"):
        cui = _do_cui_search(api, related_concept["rootSource"], related_concept["ui"])
        if cui:
            return cui

    # check other relations
    for related_concept in get_related("RO"):
        cui = _do_cui_search(api, related_concept["rootSource"], related_concept["ui"])
        if cui:
            return cui

    return None


# def _get_broader_concepts(api: MetaThesaurus, cui: str) -> Iterable[str]:
#     """
#     Get broader *or synonymous* concepts. Concepts are return in order: syn first then broader
#
#     :param api: meta thesaurus
#     :param cui: starting concept
#     :return: generator over CUIs
#     """
#     allowed_relations = ("SY", "RN", "CHD")
#
#     related_concepts = api.get_related_concepts(
#         cui, relationLabels=",".join(allowed_relations)
#     )
#
#     # group by relation type
#     grouped = collections.defaultdict(list)
#     for rc in related_concepts:
#         grouped[rc["label"]].append(rc["concept"])
#
#     seen = set()
#     for rtype in allowed_relations:
#         for cui in grouped[rtype]:
#             if cui not in seen:
#                 seen.add(cui)
#                 yield cui


def get_broader_concepts(
    api: MetaThesaurus, cui: str, language: str = None
) -> Iterator[str]:
    """
    Get broader concepts. **NO GUARANTEES REGARDING RETURN ORDER**

    :param language:
    :param api: meta thesaurus
    :param cui: starting concept
    :return: generator over CUIs
    """
    allowed_relations = ("RN", "CHD")

    if language:
        add_params = dict(language=vocab_info.validate_language(language))
    else:
        # add_params = dict(includeObsolete=True,
        #                   includeSuppressible=True)
        add_params = dict()

    broader = orderedset.UniqueFIFO()

    # first get direct relations
    for rel in api.get_relations(cui):
        if rel["relationLabel"] in allowed_relations:
            rel_c = api.get_single_result(rel["relatedId"])
            broader.push(rel_c["ui"])

    # get all atom concepts of this umls concept
    atoms = api.get_atoms(cui, **add_params)

    for atom in atoms:
        sc_url = atom["sourceConcept"]
        if not sc_url:
            continue
        sc = api.get_single_result(sc_url)

        relations = list(
            api.get_source_relations(
                source_vocab=sc["rootSource"],
                concept_id=sc["ui"],
                includeRelationLabels=",".join(allowed_relations),
                **add_params,
            )
        )
        # print(f"relations={relations}")
        for rel in relations:
            source_concept = api.get_single_result(rel["relatedId"])
            broader_cui = get_cui_for(
                api, source_concept["rootSource"], source_concept["ui"]
            )
            if broader_cui:
                broader.push(broader_cui)

    yield from broader
