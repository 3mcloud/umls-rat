import logging
import os.path
from collections import defaultdict
from typing import Optional, Iterable, List, Dict

from umlsrat import vocab_info
from umlsrat.api.metathesaurus import MetaThesaurus
from umlsrat.lookup.umls import find_umls
from umlsrat.util import misc
from umlsrat.util.orderedset import UniqueFIFO

logger = logging.getLogger(os.path.basename(__file__))


def definitions_bfs(api: MetaThesaurus, start_cui: str, num_defs: int = 0,
                    target_vocabs: Optional[Iterable[str]] = None) -> List[Dict]:
    assert num_defs >= 0

    if target_vocabs:
        target_vocabs = set(target_vocabs)

    to_visit = UniqueFIFO([start_cui])
    visited = set()
    definitions = []

    allowed_relations = ('SY', 'RN', 'CHD')
    while to_visit:
        logger.info(f"numDefinitions = {len(definitions)} numToVisit = {len(to_visit)}")
        current = to_visit.peek()

        cur_defs = api.get_definitions(current)
        if target_vocabs:
            # filter defs not in target vocab
            cur_defs = [_ for _ in cur_defs
                        if _['rootSource'] in target_vocabs]

        definitions.extend(cur_defs)
        if num_defs and len(definitions) >= num_defs:
            break

        related_concepts = api.get_related_concepts(current)

        # group by relation type todo replace with util.group_data??
        grouped = defaultdict(list)
        for rc in related_concepts:
            rcuid = rc['concept']
            if rcuid not in visited and rcuid not in to_visit:
                grouped[rc['label']].append(rcuid)

        for rtype in allowed_relations:
            to_visit.push_all(grouped[rtype])

        if logger.isEnabledFor(logging.INFO):
            logger.info(f"current = {current} #defs = {len(cur_defs)}")
            msg = "RELATIONS:\n"
            for rtype in allowed_relations:
                msg += "  {}\n" \
                       "{}\n".format(rtype, "\n".join(f"    {_}" for _ in grouped[rtype]))
            logger.info(msg)

        visited.add(to_visit.pop())

    # get out the data part
    return [_.data for _ in definitions]


def find_definitions(api: MetaThesaurus,
                     vocab_name: str, code: str,
                     target_lang: str, num_defs: int = 0) -> List[str]:
    target_vocabs = vocab_info.vocabs_for_language(target_lang)
    assert target_vocabs, f"No vocabularies for language code '{target_lang}'"
    cui = find_umls(api, vocab_name, code)
    if not cui:
        return []

    defs = definitions_bfs(api,
                           start_cui=cui,
                           num_defs=num_defs,
                           target_vocabs=target_vocabs)

    return [misc.strip_tags(_['value']) for _ in defs]
