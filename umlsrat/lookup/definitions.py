import collections
import logging
import os.path
import textwrap
from typing import Optional, Iterable, List, Dict, Iterator, Callable, Set

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import graph_fn, umls
from umlsrat.lookup.graph_fn import Action
from umlsrat.util import orderedset, text
from umlsrat.vocabularies import vocab_tools

logger = logging.getLogger(os.path.basename(__file__))


def _resolve_semantic_types(api: MetaThesaurus, concept: Dict) -> Set[str]:
    """Resolve semantic type data and return the set of type names assigned to this concept"""
    type_names = set()

    sem_types = concept["semanticTypes"]
    if not sem_types:
        return type_names

    for st in sem_types:
        type_names.add(st["name"])
        st_uri = st.pop("uri", None)
        if st_uri:
            st["data"] = api.get_single_result(st_uri)

    return type_names


def clean_definition(definition: Dict) -> Dict:
    definition = definition.copy()
    value = text.clean_definition_text(definition.pop("value"))
    return dict(value=value, **definition)


def _tokens_in_common(first: str, second: str) -> int:
    t1 = text.norm_tokenize(first)
    t2 = text.norm_tokenize(second)
    common = set(t1) | set(t2)
    return len(common)


def _name_tokens_in_common(api: MetaThesaurus, cui1: str, cui2: str) -> int:
    first = api.get_concept(cui1).get("name")
    second = api.get_concept(cui2).get("name")
    return _tokens_in_common(first, second)


def definitions_bfs(
    api: MetaThesaurus,
    start_cui: str,
    get_neighbors: Callable[[MetaThesaurus, str], Iterable[str]],
    min_concepts: int = 1,
    max_distance: int = 0,
    target_vocabs: Optional[Iterable[str]] = None,
    target_lang: str = "ENG",
    preserve_semantic_type: bool = False,
) -> List[Dict]:
    """
    Do a breadth-first search over UMLS, hunting for definitions. Resulting definitions are sorted
    by length (shortest to longest).

    :param preserve_semantic_type:
    :param get_neighbors:
    :param target_lang:
    :param api: MetaThesaurus API
    :param start_cui: starting Concept ID
    :param min_concepts: stop searching after finding this many defined concepts (0 = Infinity)
    :param max_distance: maximum allowed distance from `start_cui` (0 = Infinity)
    :param target_vocabs: only allow definitions from these vocabularies
    :return: a list of Concepts with Definitions
    """
    assert api
    assert start_cui
    assert min_concepts >= 0
    assert max_distance >= 0

    # first get target vocabs based on language
    if target_vocabs:
        target_vocabs = set(target_vocabs)
        for tv in target_vocabs:
            info = vocab_tools.get_vocab_info(tv)
            assert (
                info.Language == target_lang
            ), f"Requested vocabulary {tv} is not in the target language {target_lang}"
    else:
        target_vocabs = set(vocab_tools.vocabs_for_language(target_lang))
        assert target_vocabs, f"No vocabularies for language code '{target_lang}'"

    # If we want to preserve semantic type, we need to get them for the start CUI
    start_sem_types = None
    if preserve_semantic_type:
        start_concept = api.get_concept(start_cui)
        start_sem_types = _resolve_semantic_types(api, start_concept)

    ##
    # pre visit enforces semantic type consistency
    def pre_visit(api: MetaThesaurus, current_cui: str, current_dist: int):
        if not preserve_semantic_type:
            return Action.NONE
        current_concept = api.get_concept(current_cui)
        current_sem_types = _resolve_semantic_types(api, current_concept)

        # if there is overlap: keep it. otherwise: skip it
        if current_sem_types & start_sem_types:
            return Action.NONE
        else:
            return Action.SKIP

    ##
    # visit will accumulate definitions
    ##
    defined_concepts = []

    def visit(api: MetaThesaurus, current_cui: str, current_dist: int):
        current_concept = api.get_concept(current_cui)

        defs_url = current_concept["definitions"]
        if not defs_url:
            return

        definitions = list(api.get_results(defs_url))

        # filter defs not in target vocab
        if target_vocabs:
            definitions = [_ for _ in definitions if _["rootSource"] in target_vocabs]

        if not definitions:
            return

        # clean text, sort by length, and drop duplicates
        cleaned = orderedset.UniqueFIFO(
            sorted(map(clean_definition, definitions), key=lambda _: len(_["value"])),
            keyfn=lambda _: f"{_['rootSource']}/{text.normalize(_['value'])}",
        )

        current_concept["definitions"] = cleaned.items
        _resolve_semantic_types(api, current_concept)
        current_concept["distanceFromOrigin"] = current_dist

        # reorder dict for readability
        reordered_concept = collections.OrderedDict(
            (k, current_concept.pop(k))
            for k in (
                "classType",
                "ui",
                "name",
                "distanceFromOrigin",
                "definitions",
            )
        )
        reordered_concept.update(current_concept)

        # add to defined concepts
        defined_concepts.append(reordered_concept)

    ##
    # post visit actions are based on number of definitions and current distance from origin
    def post_visit(api: MetaThesaurus, current_cui: str, current_dist: int) -> Action:
        if min_concepts and len(defined_concepts) >= min_concepts:
            return Action.STOP

        if max_distance and current_dist == max_distance:
            return Action.SKIP

        return Action.NONE

    # here we actually do the search
    graph_fn.breadth_first_search(
        api=api,
        start_cui=start_cui,
        visit=visit,
        get_neighbors=get_neighbors,
        post_visit=post_visit,
        pre_visit=pre_visit,
    )

    return defined_concepts


def cui_sort_key(api: MetaThesaurus, source_cui: str, new_cui: str):
    """Number of tokens in common with source, new CUI itself"""
    return _name_tokens_in_common(api, source_cui, new_cui), new_cui


def broader_definitions_bfs(
    api: MetaThesaurus,
    start_cui: str,
    min_concepts: int = 1,
    max_distance: int = 0,
    target_vocabs: Optional[Iterable[str]] = None,
    target_lang: str = "ENG",
    preserve_semantic_type: bool = False,
) -> List[Dict]:
    """
    Do a breadth-first search over UMLS, hunting for definitions.

    :param preserve_semantic_type:
    :param target_lang:
    :param api: MetaThesaurus API
    :param start_cui: starting Concept ID
    :param min_concepts: stop searching after finding this many defined concepts (0 = Infinity)
    :param max_distance: maximum allowed distance from `start_cui` (0 = Infinity)
    :param target_vocabs: only allow definitions from these vocabularies
    :return: a list of Concepts with Definitions
    """

    def get_neighbors(api: MetaThesaurus, cui: str) -> Iterator[str]:
        broader_cuis = umls.get_broader_concepts(api, cui, language=target_lang)
        reordered = sorted(
            broader_cuis,
            key=lambda new_cui: cui_sort_key(api, cui, new_cui),
        )
        return reordered

    return definitions_bfs(
        api=api,
        start_cui=start_cui,
        get_neighbors=get_neighbors,
        min_concepts=min_concepts,
        max_distance=max_distance,
        target_vocabs=target_vocabs,
        target_lang=target_lang,
        preserve_semantic_type=preserve_semantic_type,
    )


def narrower_definitions_bfs(
    api: MetaThesaurus,
    start_cui: str,
    min_concepts: int = 1,
    max_distance: int = 0,
    target_vocabs: Optional[Iterable[str]] = None,
    target_lang: str = "ENG",
    preserve_semantic_type: bool = False,
) -> List[Dict]:
    """
    Do a breadth-first search over UMLS, hunting for definitions.

    :param preserve_semantic_type:
    :param target_lang:
    :param api: MetaThesaurus API
    :param start_cui: starting Concept ID
    :param min_concepts: stop searching after finding this many defined concepts (0 = Infinity)
    :param max_distance: maximum allowed distance from `start_cui` (0 = Infinity)
    :param target_vocabs: only allow definitions from these vocabularies
    :return: a list of Concepts with Definitions
    """

    def get_neighbors(api: MetaThesaurus, cui: str) -> Iterator[str]:
        narrower_cuis = umls.get_narrower_concepts(api, cui, language=target_lang)
        reordered = sorted(
            narrower_cuis,
            key=lambda new_cui: cui_sort_key(api, cui, new_cui),
        )
        return reordered

    return definitions_bfs(
        api=api,
        start_cui=start_cui,
        get_neighbors=get_neighbors,
        min_concepts=min_concepts,
        max_distance=max_distance,
        target_vocabs=target_vocabs,
        target_lang=target_lang,
        preserve_semantic_type=preserve_semantic_type,
    )


def find_defined_concepts(
    api: MetaThesaurus,
    source_vocab: str = None,
    source_code: str = None,
    source_desc: str = None,
    min_concepts: int = 1,
    max_distance: int = 0,
    target_lang: str = "ENG",
    preserve_semantic_type: bool = False,
) -> List[Dict]:
    """
    Find defined concepts in UMLS which are equal to or *broader* than the provided concept.

    :param api: MetaThesaurus API
    :param source_vocab: source vocab
    :param source_code: source code
    :param source_desc: source description
    :param min_concepts: stop searching after finding this many defined concepts (0 = Infinity)
    :param max_distance: stop searching after reaching this distance from the original source concept (0 = Infinity)
    :param target_lang: target definitions in this language
    :return: a list of Concepts with Definitions
    """
    assert min_concepts >= 0
    assert max_distance >= 0

    if source_code:
        assert source_vocab, f"Must provide source vocab for code {source_code}"
    else:
        assert (
            source_desc
        ), "Must provide either source code and vocab or descriptor (source_desc)"

    if logger.isEnabledFor(logging.INFO):
        msg = f"Finding {min_concepts} {target_lang} definition(s) of"
        if source_code:
            msg = f"{msg} {source_vocab}/{source_code}"

        if source_desc:
            msg = f"{msg} [{source_desc}]"

        logger.info(msg)

    def find_broader(start_cui: str):
        data = broader_definitions_bfs(
            api,
            start_cui=start_cui,
            min_concepts=min_concepts,
            max_distance=max_distance,
            target_lang=target_lang,
        )

        return data

    cui_from_code = None
    if source_code:
        cui_from_code = umls.get_cui_for(api, source_vocab, source_code)
        if cui_from_code:
            logger.info(f"Broader BFS for base CUI {cui_from_code} ")
            defs = find_broader(cui_from_code)
            if defs:
                return defs
            logger.info("No broader concepts with definitions.")
            # NOTE: we do not want narrower concepts!
            # logger.info(f"Searching base CUI {cui_from_code} for narrower definitions")
            # defs = find_narrower(cui_from_code)
            # if defs:
            #     return defs
        else:
            logger.info(f"UMLS concept not found for {source_vocab}/{source_code}")

    # did not find the concept directly (by code)
    if source_desc:
        # if we have a source description, try to use it to find a CUI
        # Use strict matching if we were provided with a source code initially. This will happen if
        # the provided code is an MModal addition (not in original vocab).

        max_search_results = 5  # only check the top 5 results
        search_result = umls.term_search(
            api,
            term=source_desc,
            max_results=max_search_results,
            strict_match=bool(source_code),
        )

        if search_result:
            search_term = search_result["searchTerm"]
            logger.info(f"Results for term search '{search_term}'")

            # todo don't take concepts that are too far from original?
            concepts = search_result["concepts"]

            for concept in concepts:
                cui = concept["ui"]
                name = concept["name"]
                logger.info(f"Searching concept '{name}' {cui}")
                defs = find_broader(cui)
                if defs:
                    return defs

    return []


def _entry_to_string(name: str, definitions: List[Dict]) -> str:
    value = ""
    value += f"{name}\n"
    value += "=" * len(name)
    value += "\n"
    enum_defs = (
        textwrap.fill(f"{x + 1}. {datum['value']}")
        for x, datum in enumerate(definitions)
    )
    value += "\n".join(enum_defs)
    return value


def pretty_print_defs(concepts: List[Dict]) -> str:
    """
    Get pretty string for list of Description Dicts

    :param concepts: list of Description Dicts
    :return: pretty string
    """
    entries = (_entry_to_string(c["name"], c["definitions"]) for c in concepts)
    return "\n\n".join(entries)
