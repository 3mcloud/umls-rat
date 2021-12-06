import logging
import os.path
from collections import defaultdict
from typing import Optional, Iterable, List, Dict

from umlsrat import vocab_info
from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.umls import find_umls, term_search
from umlsrat.util import misc
from umlsrat.util.orderedset import UniqueFIFO, FIFO

logger = logging.getLogger(os.path.basename(__file__))


def definitions_bfs(api: MetaThesaurus, start_cui: str, num_defs: int = 0, max_distance=0,
                    target_vocabs: Optional[Iterable[str]] = None) -> List[Dict]:
    assert num_defs >= 0
    assert max_distance >= 0

    if target_vocabs:
        target_vocabs = set(target_vocabs)

    to_visit = UniqueFIFO([start_cui])
    distances = FIFO([0])

    visited = set()
    definitions = []

    allowed_relations = ('SY', 'RN', 'CHD')
    while to_visit:

        current_cui = to_visit.peek()
        current_concept = api.get_concept(current_cui)
        reduced_concept = {k: current_concept[k] for k in ('ui', 'name')}
        current_dist = distances.peek()

        cur_defs = api.get_definitions(current_cui)
        if target_vocabs:
            # filter defs not in target vocab
            cur_defs = [_ for _ in cur_defs
                        if _['rootSource'] in target_vocabs]

        # add to definitions
        for def_dict in cur_defs:
            def_dict['distance'] = current_dist
            def_dict['concept'] = reduced_concept
            definitions.append(def_dict)

        ## Finished Visiting
        visited.add(to_visit.pop())
        distances.pop()

        logger.info(f"curDistance = {current_dist} "
                    f"numDefinitions = {len(definitions)} "
                    f"numToVisit = {len(to_visit)} "
                    f"numVisited = {len(visited)}")

        if num_defs and len(definitions) >= num_defs:
            break

        if max_distance and max_distance >= current_dist:
            continue

        ## Find neighbors and add to_visit
        related_concepts = api.get_related_concepts(current_cui)

        # group by relation type
        grouped = defaultdict(list)
        for rc in related_concepts:
            rcuid = rc['concept']
            if rcuid not in visited and rcuid not in to_visit:
                grouped[rc['label']].append(rcuid)

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


def find_definitions(api: MetaThesaurus,
                     source_vocab: str, source_code: str, source_desc: str = None,
                     num_defs: int = 0, max_distance: int = 0,
                     target_lang: str = 'ENG') -> List[Dict]:
    logger.info(f"Finding definitions of {source_vocab}/{source_code} [{source_desc}]")
    target_vocabs = vocab_info.vocabs_for_language(target_lang)
    assert target_vocabs, f"No vocabularies for language code '{target_lang}'"

    def do_bfs(start_cui: str):
        assert start_cui
        data = definitions_bfs(api,
                               start_cui=start_cui,
                               num_defs=num_defs,
                               max_distance=max_distance,
                               target_vocabs=target_vocabs)
        for datum in data:
            datum['value'] = misc.strip_tags(datum['value'])

        return data

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
            for concept in search_result['concepts']:
                cui = concept['ui']
                logger.info(f"Searching term CUI {cui}")
                defs = do_bfs(cui)
                if defs:
                    return defs

    return []
