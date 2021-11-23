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


class DefinitionsLookup(Lookup):
    def __init__(self, auth: Authenticator):
        super(DefinitionsLookup, self).__init__(auth=auth)
        self.clu = ConceptLookup(auth)

    def _check_for_definitions(self, cuid: str):
        # https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0155502/definitions?
        results = get_result(self.auth,
                             f"https://uts-ws.nlm.nih.gov/rest/content/{self.version}/CUI/{cuid}/definitions")
        if results is None:
            return None

        return [r['value'] for r in results]

    def _get_definitions(self, result: Result):
        concept = result['concept']
        if concept:
            concept = concept.pop()
            return self._check_for_definitions(concept['ui'])

        concepts = result['concepts']
        if concepts:
            for c in concepts:
                defs = self._check_for_definitions(c['ui'])
                if defs:
                    return defs

        return []

    def get_definitions(self, result: Result):
        ids = self._get_definitions(result)
        if ids:
            return ids

        # look in parents?

        parents = result['parents']
        assert parents
        for p in parents:
            ids = self._get_definitions(p)
            if ids:
                return ids

        for p in parents:
            ids = self.get_definitions(p)
            if ids:
                return ids

    def find(self, snomed_concept: str):
        res = self.clu.find(snomed_concept)

        return self.get_definitions(res)
