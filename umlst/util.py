from typing import Dict, Iterable

from umlst.auth import Authenticator


def result_iterator(result_obj: Dict) -> Iterable[Dict]:
    the_result = result_obj["result"]
    if "results" in the_result:
        yield from the_result["results"]
    else:
        yield the_result


class Result(Authenticator):
    def __init__(self, api_key):
        super(Result, self).__init__(api_key=api_key)
