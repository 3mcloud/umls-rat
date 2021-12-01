import logging
import os.path
from collections import defaultdict
from typing import List, Dict, Optional, Iterable

from umlst.api import Result, API
from umlst.util import Vocabularies

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
    :param source_vocab: from util.Vocabularies
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


class FIFO(object):
    def __init__(self, iterable: Iterable):
        self._uniq = set()
        self._list = list()
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
                    target_vocabs: Optional[Iterable[str]] = None):
    assert num_defs >= 0

    if target_vocabs:
        target_vocabs = set(target_vocabs)

    to_visit = FIFO([start_cui])
    visited = set()
    definitions = []

    allowed_relations = ('SY', 'RN', 'CHD')
    while to_visit:
        logger.info(f"numToVisit = {len(to_visit)}")
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

    return definitions


def definitions_for_cui(api: API, cui: str):
    definitions = api.get_definitions(cui)
    if definitions: return definitions

    related_concepts = api.get_related_concepts(cui)
    # group by relation type
    grouped = defaultdict(list)
    for rc in related_concepts:
        grouped[rc['label']].append(rc['concept'])

    def definitions_for_relations(label: str):
        x = sum((api.get_definitions(_) for _ in grouped[label]), [])
        print(f'{label}: {x}')
        return x

    print("IM HERE")

    # is a synonym of
    sy_defs = definitions_for_relations('SY')
    if sy_defs: return sy_defs

    # is narrower than
    rn_defs = definitions_for_relations('RN')
    if rn_defs: return rn_defs

    # is a child of
    chd_defs = definitions_for_relations('CHD')
    if chd_defs: return chd_defs

    ### time to go deeper ###
    for related_cui in grouped['RN'] + grouped['CHD']:
        pass

    raise AssertionError("Disaster!!!!")


def find_definitions(api: API, source_vocab: str, concept_id: str) -> List[Dict]:
    cui = find_umls(api, source_vocab, concept_id)
    defs = definitions_for_cui(api, cui)
    return defs


NON_ENGLISH = {"MSHSPA", "MSHPOR", "MSHSWE", "MSHCZE"}


class Lookup(object):
    def __init__(self, api: API):
        self.api = api
        self.version = 'current'


class ConceptLookup(Lookup):
    def __init__(self, api: API):
        super(ConceptLookup, self).__init__(api=api)

    def find(self, source_vocab: str, concept_id: str) -> Result:
        """
        /content/current/source/SNOMEDCT_US/9468002
        """
        uri = f'http://uts-ws.nlm.nih.gov/rest/content/{self.version}/source/{source_vocab}/{concept_id}'
        results = self.api.get_results(uri)

        assert len(results) == 1, "Should only get one concept per CID"

        return results[0]


class DefinitionsLookup(Lookup):
    def __init__(self, api: API):
        super(DefinitionsLookup, self).__init__(api=api)
        self.clu = ConceptLookup(api)

    def _get_defs_for_concept(self, result: Result):
        return self.api.get_definitions(result['ui'])

    def _defs_for_result(self, result: Result):
        concept = result['concept']
        if concept:
            concept = concept.pop()
            defs = self._defs_for_result(concept)
            if defs:
                return defs

        concepts = result['concepts']
        if concepts:
            for c in concepts:
                defs = self._get_defs_for_concept(c)
                if defs:
                    return defs

        return []

    def get_definitions(self, result: Result):
        defs = self._defs_for_result(result)
        if defs: return defs

        # look in parent concepts
        parents = result['parents']
        if not parents:
            # no parents; check relations
            relations = result['relations']
            # print(relations)
            sy_rels = [_ for _ in relations if _['relationLabel'] == 'SY']
            if not sy_rels:
                raise ValueError(f"No parents or SY relations for result:\n{result}")
            for rel in sy_rels:
                rel_res = rel['relatedId']
                assert len(rel_res) == 1
                defs = self.get_definitions(rel_res[0])
                if defs:
                    return defs
            raise ValueError("Could not find definitions")

        assert parents, f"No parents for\n: {result}"
        for p in parents[::-1]:
            defs = self._defs_for_result(p)
            if defs:
                return defs

        for p in parents:
            defs = self.get_definitions(p)
            if defs:
                return defs

    def find_all(self, snomed_concept: str) -> List:
        res = self.clu.find(Vocabularies.SNOMEDCT, snomed_concept)

        return self.get_definitions(res)

    def find_best(self, snomed_concept_id: str) -> str:
        ds = self.find_all(snomed_concept_id)
        # filter out non english
        longest_by_source = dict()  # type: Dict[str,str]
        for d in ds:
            source, value = d['rootSource'], d['value']
            incumbent = longest_by_source.get(source)
            if incumbent is None or len(value) > len(incumbent):
                longest_by_source[source] = value

        if "MSH" in longest_by_source:
            return longest_by_source["MSH"]

        english_only = {k: v for k, v in longest_by_source.items() if k not in NON_ENGLISH}
        assert english_only, "No English language descriptions!!"
        # choose the longest TODO something else?
        s = sorted(english_only.values(),
                   key=len,
                   reverse=True)
        return s[0]
