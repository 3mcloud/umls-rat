import json
import logging
import os.path
from typing import Optional, Dict, List, Iterator, Iterable

from umlsrat.api import cui_order
from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.util import text

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
    Search for a term in UMLS. Increasing the flexibility of the search with each iteration.

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
    api: MetaThesaurus, source_vocab: str, concept_id: str, desc: str = None, **kwargs
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


def get_cuis_for(api: MetaThesaurus, source_vocab: str, source_ui: str) -> List[str]:
    """
    Get UMLS CUIs for a source concept.

    **Remember** there can be more than one CUI associated with
    a given source concept.

    Try the following in order until we find some CUIs:

    #. Search for this concept using search API
    #. Same search including Obsolete and Suppressible
    #. Get source-asserted synonymous (SY-related) concepts and search for those concepts

    :param api: MetaThesaurus
    :param source_vocab: source vocabulary e.g. SNOMED
    :param source_ui: concept ID in the source vocab
    :return: CUI or None if not found
    """

    assert source_ui
    source_vocab = api.validate_source_abbrev(source_vocab)

    cuis = _do_cui_search(api, source_vocab, source_ui)
    if cuis:
        return cuis

    ## might have an obsolete concept
    cuis = _do_cui_search(
        api, source_vocab, source_ui, includeObsolete=True, includeSuppressible=True
    )
    if cuis:
        return cuis

    def get_source_related(label: str):
        relations = api.get_source_relations(
            source_vocab=source_vocab,
            concept_id=source_ui,
            includeRelationLabels=label,
        )

        concepts = [
            api.session.get_single_result(rel["relatedId"]) for rel in relations
        ]

        return [(_["rootSource"], _["ui"]) for _ in concepts]

    # check synonyms
    for rc_source, rc_ui in get_source_related("SY"):
        cuis = _do_cui_search(api, rc_source, rc_ui)
        if cuis:
            return cuis

    return []


def _get_related_cuis(
    api: MetaThesaurus,
    cui: str,
    allowed_relations: Iterable[str],
    language: str = None,
    **add_params,
) -> Iterator[str]:
    """
    Get related concepts. **NO GUARANTEES REGARDING RETURN ORDER**

    :param api: meta thesaurus
    :param cui: starting concept CUI
    :param allowed_relations: relations of interest
    :param language: language of relations?
    :param add_params: additional parameters to be passed to the call
    :return: generator yielding CUIs
    """

    seen = {cui}

    def maybe_yield(next_cui: str):
        if next_cui:
            if next_cui not in seen:
                yield next_cui
            seen.add(next_cui)

    if language:
        add_params["language"] = api.validate_language_abbrev(language)

    # first get direct relations
    for rel in api.get_relations(cui, **add_params):
        if rel["relationLabel"] in allowed_relations:
            rel_c = api.session.get_single_result(rel["relatedId"])
            yield from maybe_yield(rel_c["ui"])

    # get all atom concepts of this umls concept
    atoms = api.get_atoms(cui, **add_params)

    for atom in atoms:
        code_url = atom["code"]
        if not code_url:
            raise ValueError("'code' is not available")

        if code_url.endswith("NOCODE"):
            continue

        code = api.session.get_single_result(code_url)
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
            related = api.session.get_single_result(rel["relatedId"])

            if related.get("concept"):
                concepts = (api.session.get_single_result(related["concept"]),)
            elif related.get("concepts"):
                concepts = api.session.get_results(related["concepts"])
            else:
                raise ValueError(f"Malformed result has no concept(s)\n{related}")

            for related_concept in concepts:
                yield from maybe_yield(related_concept["ui"])


def get_related_cuis(
    api: MetaThesaurus,
    cui: str,
    allowed_relations: Iterable[str],
    language: str = None,
) -> List[str]:
    """
    Get CUIs for *all* related concepts.

    Concepts must be related via ``allowed_relations``. If no related concepts are
    found, try Obsolete and Suppressible.

    CUIs are returned in a fixed order.

    :param api: meta thesaurus
    :param cui: starting concept CUI
    :param allowed_relations: relations of interest
    :param language: language of relations?

    :return: list of CUIs
    """

    related_cuis = list(
        _get_related_cuis(
            api=api, cui=cui, allowed_relations=allowed_relations, language=language
        )
    )

    if not related_cuis:
        related_cuis = list(
            _get_related_cuis(
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


def get_broader_cuis(api: MetaThesaurus, cui: str, language: str = None) -> List[str]:
    """
    Get CUIs for broader, related concepts.

    CUIs are returned in a fixed order.

    :param api: meta thesaurus
    :param cui: starting concept CUI
    :param language: language of relations?
    :return: list of CUIs
    """
    return get_related_cuis(
        api=api, cui=cui, allowed_relations=("RN", "CHD"), language=language
    )


def get_narrower_cuis(api: MetaThesaurus, cui: str, language: str = None) -> List[str]:
    """
    Get CUIs for narrower, related concepts.

    CUIs are returned in a fixed order.

    :param api: meta thesaurus
    :param cui: starting concept CUI
    :param language: language of relations?
    :return: list of CUIs
    """
    return get_related_cuis(
        api=api, cui=cui, allowed_relations=("RB", "PAR"), language=language
    )
