import logging
import os.path
from collections import defaultdict
from typing import Optional, Iterable, List, Dict

from umlsrat.api import Result, API

logger = logging.getLogger(os.path.basename(__file__))


def _get_umls_concept(result: Result) -> Optional[Result]:
    for c_field in ('concept', 'concepts'):
        concept_res = result[c_field]
        if not concept_res: continue
        for c in concept_res:
            # check for valid UI
            if c['ui']:
                return c


def _find_umls(result: Result) -> Result:
    umls = _get_umls_concept(result)
    if umls: return umls

    # if we didn't find a UMLS concept directly, there should be a SY relation
    relations = result['relations']
    sy_rels = [_ for _ in relations if _['relationLabel'] == 'SY']
    if not sy_rels:
        raise ValueError(f"No parents or SY relations for:\n{result}")

    for rel in sy_rels:
        rel_res = rel['relatedId']
        assert len(rel_res) == 1
        return _get_umls_concept(rel_res[0])

    raise ValueError(f"Impossible to find UMLS concept for:\n{result}")


def find_umls(api: API, source_vocab: str, concept_id: str) -> str:
    """
    Get the UMLS CUI for a concept from a source vocabulary.
    """
    # uri = f"https://uts-ws.nlm.nih.gov/rest/search/current"
    # add_params = (
    #     KeyValuePair('string', concept_id),
    #     KeyValuePair('sabs', source_vocab),
    #     KeyValuePair('inputType', 'code'),
    #     KeyValuePair('searchType', 'exact'),
    #     KeyValuePair('includeObsolete', 'true'),
    #     KeyValuePair('includeSuppressible', 'true'),
    # )
    # search_res = api.get_single_result(uri, add_params)
    # concept_res = search_res['uri'].pop()
    # return concept_res
    source_res = api.get_source_concept(source_vocab, concept_id)
    assert source_res

    concept_res = _find_umls(source_res)
    return concept_res['ui']


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


def definitions_bfs(api: API, start_cui: str, num_defs: int = 0,
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
