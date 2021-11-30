import copy
import functools
import json
from collections import namedtuple
from typing import Dict, List, Optional, Tuple

import requests

from umlst.auth import Authenticator

KeyValuePair = namedtuple('KeyValuePair', ('key', 'value'))


class API(object):
    def __init__(self, auth: Authenticator):
        self.auth = auth
        self.version = 'current'
        self._rest_uri = 'https://uts-ws.nlm.nih.gov/rest'

    @functools.lru_cache()
    def _get_result(self, uri: str,
                    add_params: Optional[Tuple[KeyValuePair]] = None) -> List['Result']:
        params = {'ticket': self.auth.get_ticket()}
        if add_params:
            params.update({str(key): str(value) for key, value in add_params})

        r = requests.get(uri, params=params, verify=False)
        if r.status_code != 200:
            print(f"Request failed: {r.content}")
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

    def get_results(self, uri: str,
                    add_params: Optional[Tuple[KeyValuePair]] = None) -> List['Result']:
        """Get data from arbitrary URI wrapped in a list of Results"""
        return copy.deepcopy(self._get_result(uri, add_params))

    def get_single_result(self, uri: str,
                          add_params: Optional[Tuple[KeyValuePair]] = None) -> Optional['Result']:
        """When you know there will only be one coming back"""
        res = self.get_results(uri, add_params)
        assert len(res) < 2, f"Expected < 2 results got {len(res)}"

        if res:
            return res.pop()
        else:
            return None

    @property
    def _start_uri(self) -> str:
        return f'{self._rest_uri}/content/{self.version}'

    def get_umls_concept(self, cui: str) -> 'Result':
        """https://documentation.uts.nlm.nih.gov/rest/concept/"""
        uri = f'{self._start_uri}/CUI/{cui}'
        return self.get_single_result(uri)

    def get_definitions(self, cui: str):
        """https://documentation.uts.nlm.nih.gov/rest/definitions/index.html"""
        uri = f'{self._start_uri}/CUI/{cui}/definitions'
        return self.get_results(uri)


_NONE = "NONE"


class Result(object):
    def __init__(self, api: API, data: Dict):
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
