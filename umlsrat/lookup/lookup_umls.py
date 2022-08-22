import json
import logging
import os.path
from typing import Optional, Dict, List, Iterator, Iterable

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util import text, cui_order

logger = logging.getLogger(os.path.basename(__file__))


def get_concept_name(api: MetaThesaurus, cui: str) -> Optional[str]:
    """
    Get the name for a CUI.

    :param api: api object
    :param cui: the cui
    :return: concept name or None if it's not set
    """
    return api.get_concept(cui).get("name", None)


def _term_search(api: MetaThesaurus, term: str, max_results: int) -> Dict:
    for search_type in ("words", "normalizedWords", "approximate"):
        for input_type in ("sourceConcept", "sourceDescriptor"):
            search_params = dict(
                inputType=input_type,
                searchType=search_type,
                pageSize=min(25, max_results),
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
    Search for a term in UMLS. Increase the flexibility of the search with each iteration.

    Pseudo-Python code looks like this:

    .. code-block:: python

        for search_type in ("words", "normalizedWords", "approximate"):
            for input_type in ( "sourceConcept", "sourceDescriptor"):
                # Search for the term with above params.
                api.search(term, ...)
                # If found, return.
                ...

    See: :py:func:`umlsrat.api.metathesaurus.MetaThesaurus.search`

    :param api: api object
    :param term: the term to search for
    :param max_results: maximum number of results (default: 1000)
    :param strict_match: only allow strict matches (default: False)
    :return: search result
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
    api: MetaThesaurus, source_vocab: str, concept_id: str, **kwargs
) -> List[str]:
    search_params = dict(
        inputType="sourceUi",
        searchType="exact",
        sabs=source_vocab,
    )
    search_params.update(kwargs)
    results = list(api.search(query=concept_id, **search_params))

    cuis = [_["ui"] for _ in results]

    ordered = sorted(cuis, key=cui_order.relation_count(api, dsc=False))
    return ordered


def get_cuis_for(api: MetaThesaurus, source_vocab: str, concept_id: str) -> List[str]:
    """
    Get UMLS CUIs for a source concept.

    **Remember** there can be more than one CUI associated with
    a given source concept.

    Try the following in order until we find some CUIs:

    #. Search for this concept using search API
    #. Same search including Obsolete and Suppressible

    :param api: MetaThesaurus
    :param source_vocab: source vocabulary e.g. SNOMED
    :param concept_id: concept ID in the source vocab
    :return: CUI or None if not found
    """

    assert concept_id
    source_vocab = api.validate_source_abbrev(source_vocab)

    cuis = _do_cui_search(api, source_vocab, concept_id)
    if cuis:
        return cuis

    ## might have an obsolete concept
    cuis = _do_cui_search(
        api, source_vocab, concept_id, includeObsolete=True, includeSuppressible=True
    )
    if cuis:
        return cuis

    # we cannot find any CUIs for this concept
    return []


def _concepts_for_obj(api: MetaThesaurus, obj: Dict) -> List[Dict]:
    if obj.get("classType") == "Concept":
        return [obj]

    if "concept" in obj:
        return [api.session.get_single_result(obj["concept"])]
    elif "concepts" in obj:
        return api.session.get_results(obj["concepts"])
    else:
        raise ValueError(f"No concepts for atom:\n{obj}")


def _get_source_related_concepts(
    api: MetaThesaurus,
    cui: str,
    allowed_relation_str: str,
    language: str = None,
    **add_params,
) -> Iterator[Dict]:
    # get all atoms associated with this umls concept
    base_atoms = api.get_atoms_for_cui(cui, language=language, **add_params)

    for base_atom in base_atoms:
        if base_atom.get("rootSource") == "MTH":
            # place-holder atoms for metathesaurus
            continue

        code_url = base_atom["code"]
        if not code_url:
            raise ValueError("'code' is not available")

        if code_url.endswith("NOCODE"):
            # this is strange
            logger.debug(
                "NOCODE associated with atom:\n%s", json.dumps(base_atom, indent=2)
            )
            continue

        source_code_atom = api.session.get_single_result(code_url)
        if not source_code_atom:
            logger.warning(
                f"Got null code atom for {code_url} from\n{json.dumps(base_atom, indent=2)}"
            )
            # dead end
            continue

        source_relations = list(
            api.get_source_relations(
                source_vocab=source_code_atom["rootSource"],
                concept_id=source_code_atom["ui"],
                includeRelationLabels=allowed_relation_str,
                **add_params,
            )
        )

        for rel in source_relations:
            if "relatedId" not in rel:
                # dead end
                continue

            related_atom = api.session.get_single_result(rel["relatedId"])

            for related_concept in _concepts_for_obj(api, related_atom):
                yield related_concept


def _get_related_cuis(
    api: MetaThesaurus,
    cui: str,
    allowed_relations: Iterable[str],
    include_source_relations: bool,
    sabs: str,
    language: str,
    **add_params,
) -> Iterator[str]:
    """
    Get related concepts -- either direct (UMLS) relations or those related in a source vocab.
    **NO GUARANTEES REGARDING RETURN ORDER**

    :param api: meta thesaurus
    :param cui: starting concept CUI
    :param allowed_relations: relations of interest
    :param language: target language
    :param add_params: additional parameters passed to internal calls
    :return: generator yielding CUIs
    """

    seen = {cui}

    def yield_unique_concept_ui(next_concept: Dict):
        if not next_concept:
            return

        next_cui = next_concept["ui"]
        if not next_cui:
            return

        if next_cui not in seen:
            yield next_cui
            seen.add(next_cui)

    sabs_str = api.get_sabs_str(language, sabs)

    allowed_relation_str = ",".join(sorted(allowed_relations))

    ##
    # First get direct relations
    ##
    for rel in api.get_relations(
        cui,
        sabs=sabs_str,
        includeRelationLabels=allowed_relation_str,
        **add_params,
    ):
        atom = api.session.get_single_result(rel["relatedId"])
        for concept in _concepts_for_obj(api, atom):
            yield from yield_unique_concept_ui(concept)

    if not include_source_relations:
        return

    ##
    # Find all concepts related via an associated source atom;
    ##
    for related_concept in _get_source_related_concepts(
        api,
        cui=cui,
        allowed_relation_str=allowed_relation_str,
        language=language,
        **add_params,
    ):
        yield from yield_unique_concept_ui(related_concept)


def get_related_cuis(
    api: MetaThesaurus,
    cui: str,
    allowed_relations: Iterable[str],
    include_source_relations: bool = False,
    language: str = None,
    sabs: str = None,
) -> List[str]:
    """
    Get CUIs for related concepts.

    Concepts must be related via ``allowed_relations``. If no related concepts are
    found, try Obsolete and Suppressible.

    CUIs are returned in a fixed order.


    :param api: meta thesaurus
    :param cui: starting concept CUI
    :param allowed_relations: relations of interest
    :param include_source_relations: include CUIs related by atomic source relations
    :param language: target language
    :param sabs: comma separated list of source abbreviations

    :return: list of CUIs
    """

    related_cuis = list(
        _get_related_cuis(
            api=api,
            cui=cui,
            allowed_relations=allowed_relations,
            include_source_relations=include_source_relations,
            sabs=sabs,
            language=language,
        )
    )

    if not related_cuis:
        related_cuis = list(
            _get_related_cuis(
                api=api,
                cui=cui,
                allowed_relations=allowed_relations,
                include_source_relations=include_source_relations,
                sabs=sabs,
                language=language,
                includeObsolete=True,
                includeSuppressible=True,
            )
        )

    ordered = sorted(related_cuis)
    return ordered


def get_broader_cuis(
    api: MetaThesaurus,
    cui: str,
    include_source_relations: bool = False,
    language: str = None,
    sabs: str = None,
) -> List[str]:
    """
    Get CUIs for broader, related concepts.

    CUIs are returned in a fixed order.


    :param api: meta thesaurus
    :param cui: starting concept CUI
    :param include_source_relations: include CUIs related by atomic source relations
    :param language: target language
    :param sabs: comma separated list of source abbreviations
    :return: list of CUIs
    """
    return get_related_cuis(
        api=api,
        cui=cui,
        allowed_relations=("RN", "CHD"),
        include_source_relations=include_source_relations,
        language=language,
        sabs=sabs,
    )


def get_narrower_cuis(
    api: MetaThesaurus,
    cui: str,
    include_source_relations: bool = False,
    language: str = None,
    sabs: str = None,
) -> List[str]:
    """
    Get CUIs for narrower, related concepts.

    CUIs are returned in a fixed order.

    :param api: meta thesaurus
    :param cui: starting concept CUI
    :param include_source_relations: include CUIs related by atomic source relations
    :param language: target language
    :param sabs: comma separated list of source abbreviations
    :return: list of CUIs
    """
    return get_related_cuis(
        api=api,
        cui=cui,
        allowed_relations=("RB", "PAR"),
        include_source_relations=include_source_relations,
        language=language,
        sabs=sabs,
    )
