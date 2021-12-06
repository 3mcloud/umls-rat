import copy
import functools
import json
import logging
from collections import namedtuple
from typing import Dict, List, Optional, Tuple

from umlsrat.api import verified_requests
from umlsrat.api.auth import Authenticator
from umlsrat.vocab_info import validate_vocab_abbrev

KeyValuePair = namedtuple('KeyValuePair', ('key', 'value'))


class MetaThesaurus(object):
    def __init__(self, api_key: str):
        self.auth = Authenticator(api_key)
        self.version = 'current'
        self._rest_uri = 'https://uts-ws.nlm.nih.gov/rest'

    @property
    def logger(self):
        return logging.getLogger(self.__class__.__name__)

    @functools.lru_cache(maxsize=None)
    def _get_result(self, uri: str,
                    add_params: Optional[Tuple[KeyValuePair, ...]] = None) -> List['Result']:
        params = {'ticket': self.auth.get_ticket()}
        if add_params:
            params.update({str(key): str(value) for key, value in add_params})

        r = verified_requests.get(uri, params=params)
        if r.status_code != 200:
            self.logger.debug(f"Request failed: {r.content}")
            return []

        data = r.json()
        the_result = data["result"]
        if "results" in the_result:
            the_result = the_result["results"]

        if isinstance(the_result, List):
            return [Result(self, elem) for elem in the_result]
        elif isinstance(the_result, Dict):
            return [Result(self, the_result)]
        else:
            raise AssertionError(f"WTF type is this? {type(the_result)}")

    def get_results(self, uri: str, **params) -> List['Result']:
        """Get data from arbitrary URI wrapped in a list of Results"""
        add_params = tuple(
            KeyValuePair(str(k), str(v)) for k, v in params.items()
        )
        return copy.deepcopy(self._get_result(uri, add_params))

    def get_single_result(self, uri: str, **params) -> Optional['Result']:
        """When you know there will only be one coming back"""
        res = self.get_results(uri, **params)
        assert len(res) < 2, f"Expected < 2 results got {len(res)}"

        if res:
            return res.pop()
        else:
            return None

    #### UMLS ####
    @property
    def _start_uri(self) -> str:
        """http://uts-ws.nlm.nih.gov/rest/content/{self.version}"""
        return f'{self._rest_uri}/content/{self.version}'

    def get_concept(self, cui: str) -> 'Result':
        """https://documentation.uts.nlm.nih.gov/rest/concept/index.html"""
        uri = f'{self._start_uri}/CUI/{cui}'
        return self.get_single_result(uri)

    def get_definitions(self, cui: str):
        """https://documentation.uts.nlm.nih.gov/rest/definitions/index.html"""
        uri = f'{self._start_uri}/CUI/{cui}/definitions'
        return self.get_results(uri)

    def get_relations(self, cui: str):
        """https://documentation.uts.nlm.nih.gov/rest/relations/index.html"""
        uri = f'{self._start_uri}/CUI/{cui}/relations'
        return self.get_results(uri)

    def get_related_concepts(self, cui: str):
        """
        I see what you mean. We don't have a documented way to recreate what the web interface does without making several calls, but the web interface uses:

        https://uts-api.nlm.nih.gov/content/angular/current/CUI/C4517971/relatedConcepts?relationLabels=RB,PAR,RN,CHD&ticket=

        This aggregates broader and narrower relations for a particular UMLS Concept.

        Because this is not documented it may change at any time, but I don't expect it to change in the near future.
        """
        uri = f'https://uts-api.nlm.nih.gov/content/angular/current/CUI/{cui}/relatedConcepts'
        results = self.get_results(uri)
        return results

    ### Search ###
    def search(self, string: str, **params):
        uri = f'https://uts-ws.nlm.nih.gov/rest/search/{self.version}'
        results = self.get_results(uri, string=string, **params)
        return results

    ### Source Asserted ####
    def get_source_concept(self, source_vocab: str, concept_id: str):
        """
        https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/index.html
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        uri = f'{self._start_uri}/source/{source_vocab}/{concept_id}'
        return self.get_single_result(uri)


_NONE = "NONE"


class Result(object):
    """TODO REMOVE THIS OBJECT"""

    def __init__(self, api: MetaThesaurus, data: Dict):
        self.api = api
        self.data = data

    def get_uninterpreted(self, item: str):
        return self.data.get(item)

    def get_value(self, item: str):
        value = self.data.get(item)
        if isinstance(value, str):
            if value.startswith("http"):
                return self.api.get_results(value)
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

    def __eq__(self, other):
        return isinstance(other, Result) and self.data == other.data

    def __hash__(self):
        return hash(self.data)
