from typing import List, Dict

from umlst.auth import Authenticator
from umlst.result import Result, get_result


class Lookup(object):
    def __init__(self, auth: Authenticator):
        self.auth = auth
        self.version = 'current'


class ConceptLookup(Lookup):
    def __init__(self, auth: Authenticator):
        super(ConceptLookup, self).__init__(auth=auth)

    def _make_full_uri(self, source_vocab: str, concept_id: str):
        return f'http://uts-ws.nlm.nih.gov/rest/content/{self.version}/source/{source_vocab}/{concept_id}'

    def find(self, concept_id: str) -> Result:
        """
        /content/current/source/SNOMEDCT_US/9468002
        """

        results = get_result(self.auth, self._make_full_uri('SNOMEDCT_US', concept_id))
        # params = {'ticket': self.get_ticket()}
        # r = requests.get(self._make_full_uri('SNOMEDCT_US', concept_id),
        #                  params=params, verify=False)
        # if r.status_code != 200:
        #     raise ValueError(f"Request failed: {r.content}")
        #
        # rc = r.json()
        # results = list(Result(self, rc))

        assert len(results) == 1, "Should only get one concept per CID"

        return results[0]


NON_ENGLISH = {"MSHSPA", "MSHPOR", "MSHSWE", "MSHCZE"}


class DefinitionsLookup(Lookup):
    def __init__(self, auth: Authenticator):
        super(DefinitionsLookup, self).__init__(auth=auth)
        self.clu = ConceptLookup(auth)

    def _defs_for_cuid(self, cuid: str):
        # https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0155502/definitions?
        results = get_result(self.auth,
                             f"https://uts-ws.nlm.nih.gov/rest/content/{self.version}/CUI/{cuid}/definitions")
        if results is None:
            return None

        return [r.data for r in results]

    def _defs_for_result(self, result: Result):
        concept = result['concept']
        if concept:
            concept = concept.pop()
            return self._defs_for_cuid(concept['ui'])

        concepts = result['concepts']
        if concepts:
            for c in concepts:
                defs = self._defs_for_cuid(c['ui'])
                if defs:
                    return defs

        return []

    def get_definitions(self, result: Result):
        defs = self._defs_for_result(result)
        if defs:
            return defs

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
        for p in parents:
            defs = self._defs_for_result(p)
            if defs:
                return defs

        for p in parents:
            defs = self.get_definitions(p)
            if defs:
                return defs

    def find_all(self, snomed_concept: str) -> List:
        res = self.clu.find(snomed_concept)

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
