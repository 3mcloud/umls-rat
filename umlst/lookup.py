from typing import Dict

import requests

from umlst.auth import Authenticator
from umlst.util import result_iterator


class Lookup(Authenticator):
  def __init__(self, api_key: str):
    super(Lookup, self).__init__(api_key=api_key)
    self._base_version = 'current'
    self._base_uri = "http://uts-ws.nlm.nih.gov"

  def _make_full_uri(self, source_vocab: str, concept_id: str):
    return f'{self._base_uri}/rest/content/{self._base_version}/source/{source_vocab}/{concept_id}'

  def find(self, concept_id: str) -> Dict:
    """
    /content/current/source/SNOMEDCT_US/9468002
    """
    params = {'ticket': self.get_ticket()}
    r = requests.get(self._make_full_uri('SNOMEDCT_US', concept_id),
                     params=params, verify=False)
    if r.status_code != 200:
      raise ValueError(f"Request failed: {r.content}")

    rc = r.json()
    results = list(result_iterator(rc))

    assert len(results) == 1, "Should only get one concept per CID"

    return results[0]
