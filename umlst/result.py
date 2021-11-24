import functools
import json
from typing import Dict, List, Optional

import requests

from umlst.auth import Authenticator


@functools.lru_cache()
def get_result(auth: Authenticator, uri: str) -> Optional[List['Result']]:
    params = {'ticket': auth.get_ticket()}
    r = requests.get(uri, params=params, verify=False)
    # print(r.content)
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


_NONE = "NONE"


class Result(object):
    def __init__(self, auth: Authenticator, data: Dict):
        self._auth = auth
        self.data = data

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
