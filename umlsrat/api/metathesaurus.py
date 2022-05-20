import argparse
import json
import logging
from typing import Any, Dict, Iterator, List, Optional

from requests import HTTPError, Response

from umlsrat import const
from umlsrat.api.session import api_session, uncached_session
from umlsrat.vocabularies.vocab_tools import validate_vocab_abbrev

_NONE = "NONE"


def _interpret_none(value: Any):
    if isinstance(value, str):
        if value == _NONE:
            return None
        else:
            return value
    elif isinstance(value, Dict):
        return {key: _interpret_none(value) for key, value in value.items()}
    elif isinstance(value, List):
        return [_interpret_none(_) for _ in value]
    else:
        return value


def _default_extract_results(response_json: Dict) -> Optional[List[Dict]]:
    """
    Extract results from response json.
    :param response_json:
    :return:
    """
    if not response_json:
        return None

    results = response_json["result"]

    if "results" in results:
        results = results["results"]
        if len(results) == 1 and not results[0].get("ui", True):
            return None
        else:
            return results
    else:
        return results


class MetaThesaurus(object):
    """
    `UMLS MetaThesaurus API <https://documentation.uts.nlm.nih.gov/rest/home.html>`_ with caching.
    """

    def __init__(
        self,
        api_key: str,
        version: Optional[str] = None,
        use_cache: Optional[bool] = True,
    ):
        """
        Constructor.

        :param api_key: API key acquired from `here <https://uts.nlm.nih.gov/uts/signup-login>`_
        :param version: version of UMLS ('current' for latest). Defaults to :py:const:umlsrat.const.DEFAULT_UMLS_VERSION
        :param use_cache: use cache for requests
        """
        self._api_key = api_key
        if version:
            self.version = version
        else:
            self.version = const.DEFAULT_UMLS_VERSION

        self._rest_uri = "https://uts-ws.nlm.nih.gov/rest"
        self._use_cache = use_cache
        self._session = api_session() if use_cache else uncached_session()

    @staticmethod
    def add_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Add constructor arguments to parser.
        :param parser: argparse parser
        :return: the parser
        """
        group = parser.add_argument_group("MetaThesaurus")
        group.add_argument(
            "--umls-version",
            type=str,
            help="UMLS version to use",
            default=const.DEFAULT_UMLS_VERSION,
        )
        group.add_argument(
            "--no-cache", help="Do not use the cache", action="store_true"
        )
        group.add_argument("--api-key", type=str, help="API key", required=True)

        return parser

    @property
    def _logger(self):
        return logging.getLogger(self.__class__.__name__)

    def _do_get_request(self, uri: str, **params) -> Response:
        if "apiKey" in params:
            self._logger.warning(
                f"'apiKey' should not be in params! Will be overwritten..."
            )

        params["apiKey"] = self._api_key
        try:
            response = self._session.get(uri, params=params)
        except Exception as e:
            self._logger.exception("Failed to get %s", uri)
            raise e

        return response

    def _get(
        self, url: str, strict: Optional[bool] = False, **params
    ) -> Optional[Dict]:
        """
        Get data from arbitrary URI. Will return an empty list on 400 or 404
        unless `strict=True`, in which case it will raise.
        :param url: URL under http://uts-ws.nlm.nih.gov/rest
        :param params: get parameters *excluding* `ticket`
        :return: json response
        """
        assert url, "Must provide URL"

        r = self._do_get_request(url, **params)

        try:
            r.raise_for_status()
        except HTTPError as e:
            if strict:
                raise e

            self._logger.debug("Caught HTTPError: %s", e)
            if e.response.status_code == 400 or e.response.status_code == 404:
                # we interpret this as "you're looking for something that isn't there"
                return None
            else:
                raise e

        return _interpret_none(r.json())

    def _get_paginated(
        self,
        url: str,
        max_results: Optional[int] = None,
        **params,
    ) -> Iterator[Dict]:
        """
        Keep iterating through pages of results until there are no more *or* we
        reach max_results.

        :param url:
        :param max_results:
        :param params:
        :return:
        """
        assert url
        if max_results is not None:
            assert max_results > 0, "max_results must be > 0"

        response_json = self._get(url, **params)
        if not response_json:
            return

        if "pageNumber" not in response_json:
            raise ValueError(
                "Expected pagination fields in response:\n"
                "{}".format(json.dumps(response_json, indent=2))
            )

        if "pageNumber" not in params:
            params["pageNumber"] = 1
        else:
            self._logger.warning(
                "Starting pagination from page %d", params["pageNumber"]
            )

        n_yielded = 0
        while True:
            results = _default_extract_results(response_json)
            if not results:
                return

            for r in results:
                yield r
                n_yielded += 1
                if n_yielded == max_results:
                    return

            if response_json.get("pageCount", None) == params["pageNumber"]:
                # no more pages
                return

            # next page
            params = dict(pageNumber=params.pop("pageNumber") + 1, **params)
            response_json = self._get(url, **params)

    def get_results(
        self, url: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Get data from arbitrary URI. Will return an empty list on 400 or 404
        unless `strict=True` is in kwargs, in which case it will raise.

        :param url: URL under http://uts-ws.nlm.nih.gov/rest
        :param max_results: maximum number of result to return. None = no max
        :param params: parameters sent with the get request
        :return: generator yielding Dict results
        """
        return self._get_paginated(
            url=url,
            max_results=max_results,
            **params,
        )

    def get_single_result(self, url: str, **params) -> Optional[Dict]:
        """
        When you know there will only be one coming back

        :param url: URL under http://uts-ws.nlm.nih.gov/rest
        :param params: parameters sent with the get request
        :return: a Dict result or None
        """
        response_json = self._get(url, **params)
        if not response_json:
            return

        # This does happen, which is strange, but I guess that's okay
        # assert "pageNumber" not in response_json, \
        #     "Did not expect any pagination fields in response:\n" \
        #     "{}".format(json.dumps(response_json, indent=2))

        return response_json["result"]

    #### UMLS ####

    @property
    def _start_content_uri(self) -> str:
        """http://uts-ws.nlm.nih.gov/rest/content/{self.version}"""
        return f"{self._rest_uri}/content/{self.version}"

    def get_concept(self, cui: str) -> Dict:
        """
        Get a UMLS concept by CUI.

        See: https://documentation.uts.nlm.nih.gov/rest/concept/index.html

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :return: Concept Dict
        """
        assert cui
        uri = f"{self._start_content_uri}/CUI/{cui}"
        return self.get_single_result(uri)

    def get_definitions(
        self, cui: str, max_results: Optional[int] = None
    ) -> Iterator[Dict]:
        """
        Get the definitions for a concept.

        See: https://documentation.uts.nlm.nih.gov/rest/definitions/index.html

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Definition Dicts
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/definitions"
        return self.get_results(uri, max_results=max_results)

    def get_relations(
        self, cui: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Get relations for a concept

        See: https://documentation.uts.nlm.nih.gov/rest/relations/index.html

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Relation Dicts
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/relations"
        return self.get_results(uri, max_results=max_results, **params)

    def get_ancestors(
        self, aui: str, max_results: Optional[int] = None
    ) -> Iterator[Dict]:
        """
        Get ancestors of an Atom

        See: https://documentation.uts.nlm.nih.gov/rest/atoms/ancestors-and-descendants/index.html

        :param aui: Atom Unique Identifier (AUI) for the UMLS Atom
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Concept Dicts
        """
        assert aui.startswith("A"), f"Invalid AUI '{aui}'"
        uri = f"{self._start_content_uri}/AUI/{aui}/ancestors"
        return self.get_results(uri, max_results=max_results)

    def get_atoms(
        self, cui: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Get Atoms for a concept

        See: https://documentation.uts.nlm.nih.gov/rest/atoms/index.html

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :return: list of Relation Dicts
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/atoms"
        return self.get_results(uri, max_results=max_results, **params)

    ###
    # Search
    ###

    def search(
        self, string: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Search UMLS!

        See: https://documentation.uts.nlm.nih.gov/rest/search/index.html

        :param string: search string
        :param max_results: maximum number of result to return. None = no max
        :param params: additional get request params
        :return: generator over search results
        """
        uri = f"https://uts-ws.nlm.nih.gov/rest/search/{self.version}"
        if "string" in params:
            self._logger.warning(
                "Overwriting existing 'string' value %s", params["string"]
            )
        params["string"] = string
        return self.get_results(uri, max_results=max_results, **params)

    ###
    # Source Asserted
    ####

    def get_source_concept(self, source_vocab: str, concept_id: str) -> Optional[Dict]:
        """
        Get a "Source Asserted" concept. e.g. a concept from SNOMED, LOINC, etc

        See: https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/index.html

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: concept Dict or None
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}"
        return self.get_single_result(uri)

    def get_source_relations(
        self,
        source_vocab: str,
        concept_id: str,
        **params,
    ) -> Iterator[Dict]:
        """
        Get a "Source Asserted" relations

        See: https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/relations/index.html

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator over concept Dicts
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/relations"

        return self.get_results(uri, **params)

    def get_source_parents(
        self,
        source_vocab: str,
        concept_id: str,
    ) -> Iterator[Dict]:

        """
        Get a "Source Asserted" parents

        See: https://documentation.uts.nlm.nih.gov/rest/parents-and-children/index.html

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator over concept Dicts
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/parents"

        return self.get_results(uri)

    def get_source_ancestors(
        self,
        source_vocab: str,
        concept_id: str,
    ) -> Iterator[Dict]:
        """
        Get a "Source Asserted" ancestors

        See: https://documentation.uts.nlm.nih.gov/rest/ancestors-and-descendants/index.html

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator over concept Dicts
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/ancestors"

        return self.get_results(uri)
