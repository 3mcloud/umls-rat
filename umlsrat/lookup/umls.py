import json
import logging
import os.path
from typing import Optional, Dict, List, Iterator, Iterable

from umlsrat.api import cui_order
from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util import text
from umlsrat.vocabularies import vocab_tools

logger = logging.getLogger(os.path.basename(__file__))


def get_concept_name(api: MetaThesaurus, cui: str) -> Optional[str]:
    """
    Convenience function gets the name for a CUI.

    :param api: api object
    :param cui: the cui
    :return: concept name or None if it's not set
    """
    return api.get_concept(cui).get("name", None)


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

    hdist = text.hammingish(o_tokens, m_tokens)
    return hdist < 0.5


def term_search(
    api: MetaThesaurus,
    term: str,
    max_results: Optional[int] = 1000,
    strict_match: Optional[bool] = False,
) -> Dict:
    """
    Search for a term in UMLS.

    :param api: api object
    :param term: the term to search for
    :param max_results: maximum number of results (default: 1000)
    :param strict_match: only allow strict matches (default: False)
    :return: search result Dict
    """
    result = _term_search(api, term, max_results)

    if strict_match:
        result["concepts"] = [
            concept
            for concept in result["concepts"]
            if _is_strict_match(result["searchTerm"], concept["name"])
        ]

    return result


def _do_cui_search(
    api: MetaThesaurus, source_vocab: str, concept_id: str, desc: str = None, **kwargs
) -> List[str]:
    search_params = dict(
        inputType="sourceUi",
        searchType="exact",
        sabs=source_vocab,
    )
    search_params.update(kwargs)
    results = list(api.search(string=concept_id, **search_params))

    cuis = [_["ui"] for _ in results]

    ordered = sorted(cuis, key=cui_order.relation_count(api, dsc=False))
    return ordered


def get_cuis_for(
    api: MetaThesaurus, source_vocab: str, source_ui: str, source_desc: str = None
) -> List[str]:
    """
    Get UMLS CUI for a source concept.

    :param api: MetaThesaurus
    :param source_vocab: e.g. SNOMED
    :param source_ui: concept ID in the source vocab
    :param source_desc: description for the source code
    :return: CUI or None if not found
    """

    assert source_ui
    source_vocab = vocab_tools.validate_vocab_abbrev(source_vocab)

    cuis = _do_cui_search(api, source_vocab, source_ui)
    if cuis:
        return cuis

    ## might have an obsolete concept
    cuis = _do_cui_search(
        api, source_vocab, source_ui, includeObsolete=True, includeSuppressible=True
    )
    if cuis:
        return cuis

    def get_related(label: str):
        relations = api.get_source_relations(
            source_vocab=source_vocab,
            concept_id=source_ui,
            includeRelationLabels=label,
        )

        concepts = [api.get_single_result(rel["relatedId"]) for rel in relations]

        return [(_["rootSource"], _["ui"]) for _ in concepts]

    # check synonyms
    for rc_source, rc_ui in get_related("SY"):
        cuis = _do_cui_search(api, rc_source, rc_ui)
        if cuis:
            return cuis

    # check other relations -- this is questionable
    for rc_source, rc_ui in get_related("RO"):
        cuis = _do_cui_search(api, rc_source, rc_ui)
        if cuis:
            return cuis

    return []


def get_related_concepts(
    api: MetaThesaurus,
    cui: str,
    allowed_relations: Iterable[str],
    language: str = None,
    **add_params,
) -> Iterator[str]:
    """
    Get related concepts. **NO GUARANTEES REGARDING RETURN ORDER**

    :param allowed_relations:
    :param language:
    :param api: meta thesaurus
    :param cui: starting concept
    :return: generator over CUIs
    """

    seen = {cui}

    def maybe_yield(next_cui: str):
        if next_cui:
            if next_cui not in seen:
                yield next_cui
            seen.add(next_cui)

    if language:
        add_params["language"] = vocab_tools.validate_language(language)

    # first get direct relations
    for rel in api.get_relations(cui):
        if rel["relationLabel"] in allowed_relations:
            rel_c = api.get_single_result(rel["relatedId"])
            yield from maybe_yield(rel_c["ui"])

    # get all atom concepts of this umls concept
    atoms = api.get_atoms(cui, **add_params)

    for atom in atoms:
        code_url = atom["code"]
        if not code_url:
            raise ValueError("'code' is not available")

        if code_url.endswith("NOCODE"):
            continue

        code = api.get_single_result(code_url)
        if not code:
            raise ValueError(
                f"Got null code for {code_url} from\n" f"{json.dumps(atom, indent=2)}"
            )

        relations = list(
            api.get_source_relations(
                source_vocab=code["rootSource"],
                concept_id=code["ui"],
                includeRelationLabels=",".join(allowed_relations),
                **add_params,
            )
        )

        for rel in relations:
            related = api.get_single_result(rel["relatedId"])

            if related.get("concept"):
                concepts = (api.get_single_result(related["concept"]),)
            elif related.get("concepts"):
                concepts = api.get_results(related["concepts"])
            else:
                raise ValueError(f"Malformed result has no concept(s)\n{related}")

            for related_concept in concepts:
                yield from maybe_yield(related_concept["ui"])


def get_full_ordered_cuis(
    api: MetaThesaurus,
    cui: str,
    allowed_relations: Iterable[str],
    language: str = None,
) -> List[str]:
    """
    Get related concepts. If no related concepts are found, we will try
    Obsolete and Suppressible.

    CUIs are returned in a fixed order.

    :param allowed_relations:
    :param language:
    :param api: meta thesaurus
    :param cui: starting concept
    :return: list of CUIs
    """

    related_cuis = list(
        get_related_concepts(
            api=api, cui=cui, allowed_relations=allowed_relations, language=language
        )
    )

    if not related_cuis:
        related_cuis = list(
            get_related_concepts(
                api=api,
                cui=cui,
                allowed_relations=allowed_relations,
                language=language,
                includeObsolete=True,
                includeSuppressible=True,
            )
        )

    ordered = sorted(related_cuis, key=cui_order.cui_name_sim(api, cui))
    return ordered


def get_broader_concepts(
    api: MetaThesaurus, cui: str, language: str = None
) -> List[str]:
    """
    Get broader concepts. CUIs are returned in a fixed order.

    :param language:
    :param api: meta thesaurus
    :param cui: starting concept
    :return: list of CUIs
    """
    return get_full_ordered_cuis(
        api=api, cui=cui, allowed_relations=("RN", "CHD"), language=language
    )


def get_narrower_concepts(
    api: MetaThesaurus, cui: str, language: str = None
) -> List[str]:
    """
    Get narrower concepts. CUIs are returned in a fixed order.

    :param language:
    :param api: meta thesaurus
    :param cui: starting concept
    :return: list of CUIs
    """
    return get_full_ordered_cuis(
        api=api, cui=cui, allowed_relations=("RB", "PAR"), language=language
    )
