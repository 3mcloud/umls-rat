import logging
from typing import Dict, List, Optional, Any

from requests import HTTPError, Response
from requests_cache import CachedSession

from umlsrat.api import session
from umlsrat.api.auth import Authenticator
from umlsrat.api.session import api_session, uncached_session
from umlsrat.vocab_info import validate_vocab_abbrev

_NONE = "NONE"


def _interp_value(value: Any):
    if isinstance(value, str):
        if value == _NONE:
            return None
        else:
            return value
    else:
        return value


def _fix_res_dict(result: Dict) -> Dict:
    return {key: _interp_value(value) for key, value in result.items()}


def create_dict_list(response_json: Dict) -> List[Dict]:
    the_result = response_json["result"]
    if "results" in the_result:
        the_result = the_result["results"]

    if isinstance(the_result, Dict):
        the_result = [the_result]

    return [_fix_res_dict(_) for _ in the_result]


class MetaThesaurus(object):
    def __init__(
        self,
        api_key: str,
        version: Optional[str] = "2021AB",
        use_cache: Optional[bool] = True,
    ):
        self.auth = Authenticator(api_key)
        self.version = version
        self._rest_uri = "https://uts-ws.nlm.nih.gov/rest"
        self._session = api_session() if use_cache else uncached_session()

    @property
    def logger(self):
        return logging.getLogger(self.__class__.__name__)

    def _do_get_request(self, uri: str, **params) -> Response:
        # check the cache first
        if isinstance(self._session, CachedSession):
            response = session.check_cache(
                self._session, method="GET", url=uri, **params
            )
            if response is not None:
                return response

        params["ticket"] = self.auth.get_ticket()

        try:
            response = self._session.get(uri, params=params)
        except Exception as e:
            self.logger.exception("Failed to get %s", uri)
            raise e

        return response

    def get_results(self, uri: str, **params) -> List[Dict]:
        """Get data from arbitrary URI wrapped in a list of Results"""
        if not uri:
            return list()

        strict = params.pop("strict", False)

        if "ticket" in params:
            self.logger.warning(
                f"'ticket' should not be in params! Will be overwritten..."
            )

        r = self._do_get_request(uri, **params)

        try:
            r.raise_for_status()
        except HTTPError as e:
            if strict:
                raise e

            self.logger.warning("Caught HTTPError: %s", e)
            if e.response.status_code == 400:
                # we interpret this as "you're looking for something that isn't there"
                return []
            else:
                raise e

        return create_dict_list(r.json())

    def get_single_result(self, uri: str, **params) -> Optional[Dict]:
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
        return f"{self._rest_uri}/content/{self.version}"

    def get_concept(self, cui: str) -> Dict:
        """https://documentation.uts.nlm.nih.gov/rest/concept/index.html"""
        uri = f"{self._start_uri}/CUI/{cui}"
        return self.get_single_result(uri)

    def get_definitions(self, cui: str):
        """https://documentation.uts.nlm.nih.gov/rest/definitions/index.html"""
        uri = f"{self._start_uri}/CUI/{cui}/definitions"
        return self.get_results(uri)

    def get_relations(self, cui: str):
        """https://documentation.uts.nlm.nih.gov/rest/relations/index.html"""
        uri = f"{self._start_uri}/CUI/{cui}/relations"
        return self.get_results(uri)

    def get_related_concepts(self, cui: str):
        """
        I see what you mean. We don't have a documented way to recreate what the web interface does without making several calls, but the web interface uses:

        https://uts-api.nlm.nih.gov/content/angular/current/CUI/C4517971/relatedConcepts?relationLabels=RB,PAR,RN,CHD&ticket=

        This aggregates broader and narrower relations for a particular UMLS Concept.

        Because this is not documented it may change at any time, but I don't expect it to change in the near future.
        """
        uri = f"https://uts-api.nlm.nih.gov/content/angular/{self.version}/CUI/{cui}/relatedConcepts"
        results = self.get_results(uri)
        return results

    ### Search ###
    def search(self, string: str, **params):
        uri = f"https://uts-ws.nlm.nih.gov/rest/search/{self.version}"
        results = self.get_results(uri, string=string, **params)
        return results

    ### Source Asserted ####
    def get_source_concept(self, source_vocab: str, concept_id: str):
        """
        https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/index.html
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        uri = f"{self._start_uri}/source/{source_vocab}/{concept_id}"
        return self.get_single_result(uri)
