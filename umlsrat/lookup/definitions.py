import itertools
import logging
import os.path
import textwrap
from collections import defaultdict
from typing import Optional, Iterable, List, Dict

from umlsrat import vocab_info
from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.umls import find_umls, term_search
from umlsrat.util import misc
from umlsrat.util.orderedset import UniqueFIFO, FIFO

logger = logging.getLogger(os.path.basename(__file__))


def definitions_bfs(
    api: MetaThesaurus,
    start_cui: str,
    min_num_defs: int = 0,
    max_distance: int = 0,
    target_vocabs: Optional[Iterable[str]] = None,
) -> List[Dict]:
    assert api
    assert start_cui
    assert min_num_defs >= 0
    assert max_distance >= 0

    if target_vocabs:
        target_vocabs = set(target_vocabs)

    to_visit = UniqueFIFO([start_cui])
    distances = FIFO([0])

    visited = set()
    definitions = []

    allowed_relations = ("SY", "RN", "CHD")
    while to_visit:

        current_cui = to_visit.peek()
        current_dist = distances.peek()

        cur_defs = api.get_definitions(current_cui)
        if target_vocabs:
            # filter defs not in target vocab
            cur_defs = [_ for _ in cur_defs if _["rootSource"] in target_vocabs]

        if cur_defs:
            current_concept = api.get_concept(current_cui)
            reduced_concept = {k: current_concept[k] for k in ("ui", "name")}
            semantic_types = current_concept.get("semanticTypes")
            if semantic_types:
                type_defs = [
                    api.get_single_result(_["uri"]).get("definition")
                    for _ in semantic_types
                ]
                reduced_concept["semanticTypeDefs"] = type_defs

            # add to definitions
            for def_dict in cur_defs:
                def_dict["distance"] = current_dist
                def_dict["concept"] = reduced_concept
                definitions.append(def_dict)

        ## Finished Visiting
        visited.add(to_visit.pop())
        distances.pop()

        logger.info(
            f"curDistance = {current_dist} "
            f"numDefinitions = {len(definitions)} "
            f"numToVisit = {len(to_visit)} "
            f"numVisited = {len(visited)}"
        )

        if min_num_defs and len(definitions) >= min_num_defs:
            break

        if max_distance and max_distance >= current_dist:
            continue

        ## Find neighbors and add to_visit
        related_concepts = api.get_related_concepts(current_cui)

        # group by relation type
        grouped = defaultdict(list)
        for rc in related_concepts:
            rcuid = rc["concept"]
            if rcuid not in visited and rcuid not in to_visit:
                grouped[rc["label"]].append(rcuid)

        for rtype in allowed_relations:
            cuis = grouped[rtype]
            to_visit.push_all(cuis)
            distances.push_all([current_dist + 1] * len(cuis))

        # if logger.isEnabledFor(logging.INFO):
        #     logger.info(f"current = {current_cui} #defs = {len(cur_defs)}")
        #     msg = "RELATIONS:\n"
        #     for rtype in allowed_relations:
        #         msg += "  {}\n" \
        #                "{}\n".format(rtype, "\n".join(f"    {_}" for _ in grouped[rtype]))
        #     logger.info(msg)

    return definitions


def find_definitions(
    api: MetaThesaurus,
    source_vocab: str = None,
    source_code: str = None,
    source_desc: str = None,
    min_num_defs: int = 1,
    max_distance: int = 0,
    target_lang: str = "ENG",
) -> List[Dict]:
    """
    Find definitions in UMLS MetaThesaurus.

    :param api: base MetaThesaurus API object
    :param source_vocab: source vocab
    :param source_code: source code
    :param source_desc: source description
    :param min_num_defs: stop searching after finding this many definitions (0 = Infinity)
    :param max_distance: stop searching after reaching this distance from the original source concept (0 = Infinity)
    :param target_lang: target definitions in this language?
    :return: a list of Description objects as dictionaries
    """
    assert min_num_defs >= 0
    assert max_distance >= 0

    if source_code:
        assert source_vocab, f"Must provide source vocab for code {source_code}"
    else:
        assert (
            source_desc
        ), "Must provide either source code and vocab or descriptor (source_desc)"

    if logger.isEnabledFor(logging.INFO):
        msg = f"Finding {min_num_defs} {target_lang} definition(s) of"
        if source_code:
            msg = f"{msg} {source_vocab}/{source_code}"

        if source_desc:
            msg = f"{msg} [{source_desc}]"

        logger.info(msg)

    target_vocabs = vocab_info.vocabs_for_language(target_lang)
    assert target_vocabs, f"No vocabularies for language code '{target_lang}'"

    def do_bfs(start_cui: str):
        assert start_cui
        data = definitions_bfs(
            api,
            start_cui=start_cui,
            min_num_defs=min_num_defs,
            max_distance=max_distance,
            target_vocabs=target_vocabs,
        )
        for datum in data:
            datum["value"] = misc.strip_tags(datum["value"])

        return data

    if source_code:
        cui = find_umls(api, source_vocab, source_code)
        if cui:
            logger.info(f"Searching base CUI {cui}")
            defs = do_bfs(cui)
            if defs:
                return defs

    # did not find the concept directly (by code)
    if source_desc:
        # if we have a source description, try to use it to find a CUI
        search_result = term_search(api, source_desc)
        if search_result:
            # todo don't take concepts that are too far from original?
            for concept in search_result["concepts"]:
                cui = concept["ui"]
                logger.info(f"Searching term CUI {cui}")
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
        textwrap.fill(f"({x + 1}) {datum['value']}")
        for x, datum in enumerate(definitions)
    )
    string += "\n".join(enum_defs)
    return string


def definitions_to_string(definitions: List[Dict]) -> str:
    grouped = itertools.groupby(definitions, key=lambda _: _["concept"]["name"])
    entries = (_entry_to_string(*args) for args in grouped)
    return "\n\n".join(entries)
