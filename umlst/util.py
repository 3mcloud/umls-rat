from typing import Dict, Iterable


def result_iterator(result_obj: Dict) -> Iterable[Dict]:
  the_result = result_obj["result"]
  if "results" in the_result:
    yield from the_result["results"]
  else:
    yield the_result
