import functools
import json
from typing import Dict, List, Optional

import requests

from umlst.util import Authenticator

_NONE = "NONE"


@functools.lru_cache()
def get_result(auth: Authenticator, uri: str) -> Optional[List['Result']]:
    params = {'ticket': auth.get_ticket()}
    r = requests.get(uri, params=params, verify=False)
    print(r.content)
    if r.status_code != 200:
        print(f"Request failed: {r.content}")
        return None
    data = r.json()
    the_result = data["result"]
    if "results" in the_result:
        the_result = the_result["results"]

    if isinstance(the_result, List):
        return [Result(auth, elem) for elem in the_result]
    elif isinstance(the_result, Dict):
        return [Result(auth, the_result)]
    else:
        raise AssertionError(f"WTF type is this? {type(the_result)}")


class Result(object):
    def __init__(self, auth: Authenticator, data: Dict):
        self._auth = auth
        self.data = data

    # def __iter__(self):
    #     the_result = self.data["result"]
    #     if "results" in the_result:
    #         for data in the_result["results"]:
    #             yield Result(self._auth, data)
    #     else:
    #         yield Result(self._auth, the_result)

    def get_value(self, item: str):
        value = self.data.get(item)
        if isinstance(value, str):
            if value.startswith("http"):
                return get_result(self._auth, value)
            elif value == _NONE:
                return None
            else:
                return value
        else:
            return value

    def __getitem__(self, item):
        return self.get_value(item)

    def __str__(self):
        return json.dumps(self.data, indent=2)

    def __repr__(self):
        return str(self)


class Lookup(Authenticator):
    def __init__(self, api_key: str):
        super(Lookup, self).__init__(api_key=api_key)
        self.version = 'current'


class ConceptLookup(Lookup):
    def __init__(self, api_key: str):
        super(ConceptLookup, self).__init__(api_key=api_key)

    def _make_full_uri(self, source_vocab: str, concept_id: str):
        return f'http://uts-ws.nlm.nih.gov/rest/content/{self.version}/source/{source_vocab}/{concept_id}'

    def find(self, concept_id: str) -> Result:
        """
        /content/current/source/SNOMEDCT_US/9468002
        """

        results = get_result(self, self._make_full_uri('SNOMEDCT_US', concept_id))
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
    def __init__(self, concept_lookup: ConceptLookup):
        super(DefinitionsLookup, self).__init__(api_key=concept_lookup.api_key)
        self.clu = concept_lookup

    def _check_for_definitions(self, cuid: str):
        # https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0155502/definitions?
        results = get_result(self,
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
