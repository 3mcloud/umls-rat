import collections
import logging
import os.path
import re
import textwrap
from typing import Optional, Iterable, List, Dict, Iterator

from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup import graph_fn, umls
from umlsrat.lookup.graph_fn import Action
from umlsrat.util import misc, orderedset
from umlsrat.vocabularies import vocab_info

logger = logging.getLogger(os.path.basename(__file__))


def _resolve_semantic_types(api: MetaThesaurus, concept: Dict) -> None:
    sem_types = concept["semanticTypes"]
    if sem_types:
        for st in sem_types:
            st_uri = st.pop("uri", None)
            if st_uri:
                st["data"] = api.get_single_result(st_uri)


def _clean_up_definition_text(text: str) -> str:
    clean = misc.strip_tags(text)
    clean = re.sub(r"\s*\(NCI\)", "", clean)
    clean = re.sub(r"\[\]", "", clean)
    return clean.strip()


def _clean_up_definition(definition: Dict) -> Dict:
    definition = definition.copy()
    value = _clean_up_definition_text(definition.pop("value"))
    return dict(value=value, **definition)


def definitions_bfs(
    api: MetaThesaurus,
    start_cui: str,
    min_concepts: int = 1,
    max_distance: int = 0,
    target_vocabs: Optional[Iterable[str]] = None,
    target_lang: str = "ENG",
) -> List[Dict]:
    """
    Do a breadth-first search over UMLS, hunting for definitions.

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

    ##
    # visit will accumulate definitions
    if target_vocabs:
        target_vocabs = set(target_vocabs)
        for tv in target_vocabs:
            info = vocab_info.get_vocab_info(tv)
            assert (
                info.Language == target_lang
            ), f"Requested vocabulary {tv} is not in the target language {target_lang}"
    else:
        target_vocabs = set(vocab_info.vocabs_for_language(target_lang))
        assert target_vocabs, f"No vocabularies for language code '{target_lang}'"

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

        # strip random xml tags from definitions, and drop duplicates
        cleaned = orderedset.UniqueFIFO(
            map(_clean_up_definition, definitions),
            keyfn=lambda _: f"{_['rootSource']}/{_['value']}",
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

        if max_distance and max_distance >= current_dist:
            return Action.SKIP

        return Action.NONE

    def get_neighbors(api: MetaThesaurus, cui: str) -> Iterator[str]:
        cuis = umls.get_broader_concepts(api, cui, language=target_lang)
        return sorted(
            cuis,
            key=lambda _: (-sum(1 for _ in api.get_atoms(_, sabs="SNOMEDCT_US")), _),
        )

    # here we actually do the search
    graph_fn.breadth_first_search(
        api=api,
        start_cui=start_cui,
        visit=visit,
        get_neighbors=get_neighbors,
        post_visit=post_visit,
    )

    return defined_concepts


def find_defined_concepts(
    api: MetaThesaurus,
    source_vocab: str = None,
    source_code: str = None,
    source_desc: str = None,
    min_concepts: int = 1,
    max_distance: int = 0,
    target_lang: str = "ENG",
) -> List[Dict]:
    """
    Find definitions in UMLS MetaThesaurus.

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

    def do_bfs(start_cui: str):
        assert start_cui
        data = definitions_bfs(
            api,
            start_cui=start_cui,
            min_concepts=min_concepts,
            max_distance=max_distance,
            target_lang=target_lang,
        )

        return data

    if source_code:
        cui = umls.get_cui_for(api, source_vocab, source_code)
        if cui:
            logger.info(f"Searching base CUI {cui}")
            defs = do_bfs(cui)
            if defs:
                return defs

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
                defs = do_bfs(cui)
                if defs:
                    return defs

    return []


def _entry_to_string(name: str, definitions: List[Dict]) -> str:
    string = ""
    string += f"{name}\n"
    string += "=" * len(name)
    string += "\n"
    enum_defs = (
        textwrap.fill(f"{x + 1}. {datum['value']}")
        for x, datum in enumerate(definitions)
    )
    string += "\n".join(enum_defs)
    return string


def pretty_print_defs(concepts: List[Dict]) -> str:
    """
    Get pretty string for list of Description Dicts

    :param concepts: list of Description Dicts
    :return: pretty string
    """
    entries = (_entry_to_string(c["name"], c["definitions"]) for c in concepts)
    return "\n\n".join(entries)
