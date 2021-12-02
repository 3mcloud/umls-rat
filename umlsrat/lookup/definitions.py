import logging
import os.path
from collections import defaultdict
from typing import Optional, Iterable, List, Dict

from umlsrat.api.metathesaurus import MetaThesaurus

logger = logging.getLogger(os.path.basename(__file__))


class UniqueFIFO(object):
    def __init__(self, iterable: Optional[Iterable] = None):
        self._uniq = set()
        self._list = list()
        if iterable:
            self.push_all(iterable)

    def push(self, item):
        if item not in self._uniq:
            self._list.append(item)
            self._uniq.add(item)

    def pop(self):
        item = self._list.pop(0)
        self._uniq.discard(item)
        return item

    def peek(self):
        return self._list[0]

    def push_all(self, iterable):
        for item in iterable:
            self.push(item)

    def __len__(self):
        return len(self._list)

    def __contains__(self, item):
        return item in self._uniq

    def __str__(self):
        return str(self._list)

    def __repr__(self):
        return str(self)


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

        # group by relation type
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
