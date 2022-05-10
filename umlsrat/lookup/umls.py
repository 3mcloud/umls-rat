import logging
import os.path
import re
from typing import Optional, Dict, List, Set, Iterator, Iterable

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util import text
from umlsrat.vocabularies import vocab_tools

logger = logging.getLogger(os.path.basename(__file__))


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
                # sort by hammingish -- the UMLS search is probably better in most cases
                # txt_key = text.hammingish_partial(term)
                #
                # def sort_key(c: Dict) -> float:
                #     return txt_key(c["name"])
                #
                # concepts = sorted(concepts, key=sort_key)
                return dict(**search_params, searchTerm=term, concepts=concepts)

    return dict(searchTerm=term, concepts=[])


def _is_strict_match(original: str, matched: str) -> bool:
    o_tokens = text.norm_tokenize(original)
    m_tokens = text.norm_tokenize(matched)

    # if each is only one token and one contains the other exactly
    if len(o_tokens) == len(m_tokens) == 1 and (
        o_tokens[0] in m_tokens[0] or m_tokens[0] in o_tokens[0]
    ):
        return True

    o_set = set(o_tokens)
    m_set = set(m_tokens)

    return (
        # all original words are in matched
        (o_set & m_set) == o_set
        and
        # there are fewer than three additional words in matched
        len(m_set - o_set) < 3
    )


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
    api: MetaThesaurus, source_vocab: str, concept_id: str, **kwargs
) -> Optional[str]:
    search_params = dict(
        inputType="sourceUi",
        searchType="exact",
        sabs=source_vocab,
    )
    search_params.update(kwargs)
    results = list(api.search(string=concept_id, **search_params))

    if results:
        return results[0]["ui"]

    return None


def get_cui_for(
    api: MetaThesaurus, source_vocab: str, concept_id: str
) -> Optional[str]:
    """
    Get UMLS CUI for a source concept.

    :param api: MetaThesaurus
    :param source_vocab: e.g. SNOMED
    :param concept_id: concept ID in the source vocab
    :return: CUI or None if not found
    """

    assert concept_id
    source_vocab = vocab_tools.validate_vocab_abbrev(source_vocab)

    cui = _do_cui_search(api, source_vocab, concept_id)
    if cui:
        return cui

    ## might have an obsolete concept
    cui = _do_cui_search(
        api, source_vocab, concept_id, includeObsolete=True, includeSuppressible=True
    )
    if cui:
        return cui

    def get_related(label: str):
        relations = api.get_source_relations(
            source_vocab=source_vocab,
            concept_id=concept_id,
            includeRelationLabels=label,
        )

        concepts = [api.get_single_result(rel["relatedId"]) for rel in relations]

        return [(_["rootSource"], _["ui"]) for _ in concepts]

    # check synonyms
    for rc_source, rc_ui in get_related("SY"):
        cui = _do_cui_search(api, rc_source, rc_ui)
        if cui:
            return cui

    # check other relations
    for rc_source, rc_ui in get_related("RO"):
        cui = _do_cui_search(api, rc_source, rc_ui)
        if cui:
            return cui

    return None


def get_related_concepts(
    api: MetaThesaurus, cui: str, allowed_relations: Iterable[str], language: str = None
) -> Iterator[str]:
    """
    Get related concepts. **NO GUARANTEES REGARDING RETURN ORDER**

    :param allowed_relations:
    :param language:
    :param api: meta thesaurus
    :param cui: starting concept
    :return: generator over CUIs
    """

    if language:
        add_params = dict(language=vocab_tools.validate_language(language))
    else:
        add_params = dict()

    seen = set()

    def maybe_yield(next_cui: str):
        if next_cui and next_cui not in seen:
            yield next_cui
            seen.add(next_cui)

    # first get direct relations
    for rel in api.get_relations(cui):
        if rel["relationLabel"] in allowed_relations:
            rel_c = api.get_single_result(rel["relatedId"])
            yield from maybe_yield(rel_c["ui"])

    # get all atom concepts of this umls concept
    atoms = api.get_atoms(cui, **add_params)

    for atom in atoms:
        sc_url = atom["sourceConcept"]
        if not sc_url:
            continue
        sc = api.get_single_result(sc_url)
        if not sc:
            # this is very strange. possibly a bug? todo
            continue
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
            yield from maybe_yield(broader_cui)


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

    yield from get_related_concepts(
        api=api, cui=cui, allowed_relations=("RN", "CHD"), language=language
    )


def get_narrower_concepts(
    api: MetaThesaurus, cui: str, language: str = None
) -> Iterator[str]:
    """
    Get narrower concepts. **NO GUARANTEES REGARDING RETURN ORDER**

    :param language:
    :param api: meta thesaurus
    :param cui: starting concept
    :return: generator over CUIs
    """

    yield from get_related_concepts(
        api=api, cui=cui, allowed_relations=("RB", "PAR"), language=language
    )
