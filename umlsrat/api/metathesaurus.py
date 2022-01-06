import logging
from typing import Dict, List, Optional, Any

import requests
from requests import HTTPError, Response
from requests_cache import CachedSession, CachedResponse

from umlsrat.api.auth import Authenticator
from umlsrat.api.session import api_session, uncached_session
from umlsrat.vocabularies.vocab_info import validate_vocab_abbrev

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


def _create_dict_list(response_json: Dict) -> List[Dict]:
    the_result = response_json["result"]
    if "results" in the_result:
        the_result = the_result["results"]

    if isinstance(the_result, Dict):
        the_result = [the_result]

    return [_fix_res_dict(_) for _ in the_result]


class MetaThesaurus(object):
    """
    UMLS MetaThesaurus API. Now with caching! :)
    https://documentation.uts.nlm.nih.gov/rest/home.html
    """

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

    def _get_cached(self, method: str, url: str, **params) -> Optional[CachedResponse]:
        if not isinstance(self._session, CachedSession):
            return None

        request = requests.Request(method=method, url=url, params=params)
        request = self._session.prepare_request(request)

        # verify goes here
        key = self._session.cache.create_key(request, verify=self._session.verify)
        value = self._session.cache.get_response(key)

        return value

    def _do_get_request(self, uri: str, **params) -> Response:
        # check the cache first
        response = self._get_cached("GET", url=uri, **params)
        if response is not None:
            return response

        params["ticket"] = self.auth.get_ticket()

        try:
            response = self._session.get(uri, params=params)
        except Exception as e:
            self.logger.exception("Failed to get %s", uri)
            raise e

        return response

    def get_results(self, url: str, **params) -> List[Dict]:
        """
        Get data from arbitrary URI wrapped in a list of Results
        :param url: URL under http://uts-ws.nlm.nih.gov/rest
        :param params: get parameters *excluding* `ticket`
        :return: a list of Dict results
        """
        if not url:
            return list()

        strict = params.pop("strict", False)

        if "ticket" in params:
            self.logger.warning(
                f"'ticket' should not be in params! Will be overwritten..."
            )

        r = self._do_get_request(url, **params)

        try:
            r.raise_for_status()
        except HTTPError as e:
            if strict:
                raise e

            self.logger.debug("Caught HTTPError: %s", e)
            if e.response.status_code == 400:
                # we interpret this as "you're looking for something that isn't there"
                return []
            else:
                raise e

        return _create_dict_list(r.json())

    def get_single_result(self, url: str, **params) -> Optional[Dict]:
        """
        When you know there will only be one coming back
        :param url: URL under http://uts-ws.nlm.nih.gov/rest
        :param params: get parameters *excluding* `ticket`
        :return: a Dict result or None
        """
        res = self.get_results(url, **params)
        if not res:
            return None

        assert len(res) == 1, f"Expected 1 result got {len(res)}"
        return res[0]

    #### UMLS ####
    @property
    def _start_uri(self) -> str:
        """http://uts-ws.nlm.nih.gov/rest/content/{self.version}"""
        return f"{self._rest_uri}/content/{self.version}"

    def get_concept(self, cui: str) -> Dict:
        """
        Get a UMLS concept by CUI.
        See: https://documentation.uts.nlm.nih.gov/rest/concept/index.html
        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :return: Concept Dict
        """
        uri = f"{self._start_uri}/CUI/{cui}"
        return self.get_single_result(uri)

    def get_definitions(self, cui: str) -> List[Dict]:
        """
        Get the definitions for a concept.
        See: https://documentation.uts.nlm.nih.gov/rest/definitions/index.html
        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :return: list of Definition Dicts
        """
        uri = f"{self._start_uri}/CUI/{cui}/definitions"
        return self.get_results(uri)

    def get_relations(self, cui: str) -> List[Dict]:
        """
        Get relations for a concept
        See: https://documentation.uts.nlm.nih.gov/rest/relations/index.html
        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :return: list of Relation Dicts
        """
        uri = f"{self._start_uri}/CUI/{cui}/relations"
        return self.get_results(uri)

    def get_related_concepts(self, cui: str, **params) -> List[Dict]:
        """
        Get related concepts

        Email from NLM Support:

        I see what you mean. We don't have a documented way to recreate what the web interface does without making several calls, but the web interface uses:

        https://uts-api.nlm.nih.gov/content/angular/current/CUI/C4517971/relatedConcepts?relationLabels=RB,PAR,RN,CHD&ticket=

        This aggregates broader and narrower relations for a particular UMLS Concept.

        Because this is not documented it may change at any time, but I don't expect it to change in the near future.

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :return: list of Relation Dicts
        """
        uri = f"https://uts-api.nlm.nih.gov/content/angular/{self.version}/CUI/{cui}/relatedConcepts"
        try:
            return self.get_results(uri, **params)
        except requests.exceptions.ConnectionError as e:
            self.logger.exception(
                "Connection failed when getting related concepts! Try restricting "
                "results with 'relationLabels' e.g. relationLabels=RN,CHD"
            )
            raise e

    ### Search ###
    def search(self, string: str, **params) -> List[Dict]:
        """
        Search UMLS!
        See: https://documentation.uts.nlm.nih.gov/rest/search/index.html
        :param string: search string
        :param params: additional get request params
        :return: list of search results (Concepts?)
        """
        uri = f"https://uts-ws.nlm.nih.gov/rest/search/{self.version}"
        results = self.get_results(uri, string=string, **params)
        return results

    ### Source Asserted ####
    def get_source_concept(self, source_vocab: str, concept_id: str) -> Optional[Dict]:
        """
        Get a "Source Asserted" concept. i.e. get a concept by ID in a Vocabulary which is not UMLS
        See: https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/index.html
        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: concept Dict or None
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        uri = f"{self._start_uri}/source/{source_vocab}/{concept_id}"
        return self.get_single_result(uri)
