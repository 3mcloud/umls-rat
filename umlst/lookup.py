from typing import List, Dict, Optional

from umlst.api import Result, API
from umlst.util import Vocabularies


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


def find_umls(auth: API, source_vocab: str, concept_id: str) -> Result:
    snomed_res = ConceptLookup(auth).find(source_vocab, concept_id)
    assert snomed_res

    base_res = _find_umls(snomed_res)
    uri_res = base_res['uri']
    if uri_res:
        assert len(uri_res) == 1
        return uri_res.pop()
    else:
        return base_res


def _definitions_for_umls_result(umls: Result):
    definitions = umls.api.get_definitions(umls['ui'])
    if definitions: return definitions

    relations = umls['relations']
    if relations:
        for rel in relations:
            definitions = rel["relatedId"][0]["uri"][0]["definitions"]
            if definitions: return definitions

    raise AssertionError("Disaster!!!!")


def find_definitions(api: API, source_vocab: str, concept_id: str) -> List[Dict]:
    umls = find_umls(api, source_vocab, concept_id)
    defs = _definitions_for_umls_result(umls)
    return defs


NON_ENGLISH = {"MSHSPA", "MSHPOR", "MSHSWE", "MSHCZE"}


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
            return self._defs_for_result(result)

        concepts = result['concepts']
        if concepts:
            for c in concepts:
                defs = self._get_defs_for_concept(c)
                if defs: return defs

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
