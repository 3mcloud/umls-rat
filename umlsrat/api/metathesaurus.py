import argparse
import json
import logging
from typing import Any, Dict, Iterator, List, Optional

from requests import HTTPError

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
    `UMLS MetaThesaurus API <https://documentation.uts.nlm.nih.gov/rest/home.html>`_ interface with caching.
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
        :param use_cache: use cache for requests (default ``True``)
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

        :param parser: parser
        :return: the same parser
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

        if "apiKey" in params:
            self._logger.warning(
                f"'apiKey' should not be in params! Will be overwritten..."
            )

        params["apiKey"] = self._api_key
        try:
            response = self._session.get(url, params=params)
        except Exception as e:
            self._logger.exception("Failed to get %s", url)
            raise e

        try:
            response.raise_for_status()
        except HTTPError as e:
            if strict:
                raise e

            self._logger.debug("Caught HTTPError: %s", e)
            if e.response.status_code == 400 or e.response.status_code == 404:
                # we interpret this as "you're looking for something that isn't there"
                return None
            else:
                raise e

        return _interpret_none(response.json())

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

    def _get_results(
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

    def _get_single_result(self, url: str, **params) -> Optional[Dict]:
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

        Example

        .. code-block:: python

            api_instance.get_concept("C0009044")
            # {
            #   "ui": "C0009044",
            #   "name": "Closed fracture of carpal bone",
            #   "dateAdded": "09-30-1990",
            #   "majorRevisionDate": "03-16-2016",
            #   "classType": "Concept",
            #   "suppressible": false,
            #   "status": "R",
            #   "semanticTypes": [
            #     {
            #       "name": "Injury or Poisoning",
            #       "uri": "https://uts-ws.nlm.nih.gov/rest/semantic-network/2021AB/TUI/T037"
            #     }
            #   ],
            #   "atoms": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044/atoms",
            #   "definitions": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044/definitions",
            #   "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044/relations",
            #   "defaultPreferredAtom": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044/atoms/preferred",
            #   "atomCount": 71,
            #   "cvMemberCount": 0,
            #   "attributeCount": 0,
            #   "relationCount": 5
            # }

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/concept/index.html>`_

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :return: Concept Dict
        """
        assert cui
        uri = f"{self._start_content_uri}/CUI/{cui}"
        return self._get_single_result(uri)

    def get_definitions(
        self, cui: str, max_results: Optional[int] = None
    ) -> Iterator[Dict]:
        """
        Get the definitions for a concept.

        .. code-block:: python

            list(api.get_definitions("C0009044"))
            # [
            #   {
            #     "rootSource": "NCI",
            #     "value": "A traumatic break in one or more of the carpal bones that does not involve a break in the adjacent skin.",
            #     "classType": "Definition",
            #     "sourceOriginated": true
            #   }
            # ]

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/definitions/index.html>`_

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Definition Dicts
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/definitions"
        return self._get_results(uri, max_results=max_results)

    def get_relations(
        self, cui: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Get relations for a concept

        .. code-block:: python

            list(api.get_relations("C0009044"))
            # [
            #   {
            #     "ui": "R03033072",
            #     "suppressible": false,
            #     "sourceUi": null,
            #     "obsolete": false,
            #     "sourceOriginated": false,
            #     "rootSource": "MTH",
            #     "relationLabel": "RO",
            #     "additionalRelationLabel": "",
            #     "groupId": null,
            #     "relatedId": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009353",
            #     "relatedIdName": "Colles' Fracture",
            #     "classType": "ConceptRelation",
            #     "attributeCount": 0
            #   },
            #   ...
            # ]

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/relations/index.html>`_

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Relation Dicts
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/relations"
        return self._get_results(uri, max_results=max_results, **params)

    def get_atoms(
        self, cui: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Get Atoms for a concept.

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/atoms/index.html>`_

        .. code-block:: python

            list(api.get_atoms(cui="C0009044", language="ENG"))
            # [
            #   {
            #     "classType": "Atom",
            #     "ui": "A0243916",
            #     "sourceDescriptor": null,
            #     "sourceConcept": null,
            #     "concept": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044",
            #     "obsolete": "false",
            #     "suppressible": "false",
            #     "rootSource": "RCD",
            #     "termType": "PT",
            #     "code": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/RCD/S240.",
            #     "language": "ENG",
            #     "name": "Closed fracture of carpal bone",
            #     "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/attributes",
            #     "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/relations",
            #     "children": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/children",
            #     "descendants": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/descendants",
            #     "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/parents",
            #     "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/ancestors",
            #     "contentViewMemberships": [
            #       {
            #         "memberUri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357/member/A0243916",
            #         "name": "MetaMap NLP View",
            #         "uri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357"
            #       }
            #     ]
            #   },
            #   ...
            # ]


        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :param params: additional params passed to the GET request See `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/atoms/index.html>`_
        :return: list of Relation Dicts
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/atoms"
        return self._get_results(uri, max_results=max_results, **params)

    def get_ancestors(
        self, aui: str, max_results: Optional[int] = None
    ) -> Iterator[Dict]:
        """
        Get ancestors of an Atom

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/atoms/ancestors-and-descendants/index.html>`_

        .. code-block:: python

            list(api.get_ancestors(aui="A0243916"))

            # [
            #   {
            #     "classType": "Atom",
            #     "ui": "A0004658",
            #     "sourceDescriptor": null,
            #     "sourceConcept": null,
            #     "concept": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0016658",
            #     "obsolete": "false",
            #     "suppressible": "false",
            #     "rootSource": "RCD",
            #     "termType": "PT",
            #     "code": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/RCD/XA0FK",
            #     "language": "ENG",
            #     "name": "Fracture",
            #     "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/attributes",
            #     "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/relations",
            #     "children": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/children",
            #     "descendants": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/descendants",
            #     "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/parents",
            #     "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/ancestors",
            #     "contentViewMemberships": [
            #       {
            #         "memberUri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357/member/A0004658",
            #         "name": "MetaMap NLP View",
            #         "uri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357"
            #       }
            #     ]
            #   },
            #   ...
            # ]

        :param aui: Atom Unique Identifier (AUI) for the UMLS Atom
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Concept Dicts
        """
        assert aui.startswith("A"), f"Invalid AUI '{aui}'"
        uri = f"{self._start_content_uri}/AUI/{aui}/ancestors"
        return self._get_results(uri, max_results=max_results)

    ###
    # Search
    ###

    def search(
        self, query: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Search UMLS!

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/search/index.html>`_

        .. code-block:: python

            api.search("cheese", max_results=1)
            # [
            #   {
            #     "ui": "C0007968",
            #     "rootSource": "MTH",
            #     "uri": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0007968",
            #     "name": "Cheese"
            #   }
            # ]

        :param query: search string
        :param max_results: maximum number of result to return. None = no max
        :param params: additional get request params
        :return: generator over search results
        """
        uri = f"https://uts-ws.nlm.nih.gov/rest/search/{self.version}"
        if "string" in params:
            self._logger.warning(
                "Overwriting existing 'string' value %s", params["string"]
            )
        params["string"] = query
        return self._get_results(uri, max_results=max_results, **params)

    ###
    # Source Asserted
    ####

    def get_source_concept(self, source_vocab: str, concept_id: str) -> Optional[Dict]:
        """
        Get a "Source Asserted" concept. e.g. a concept from SNOMED, LOINC, etc

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/index.html>`_

        .. code-block:: python

            api.get_source_concept(source_vocab="snomed", concept_id="75508005")
            # {
            #   "classType": "SourceAtomCluster",
            #   "ui": "75508005",
            #   "suppressible": false,
            #   "obsolete": false,
            #   "rootSource": "SNOMEDCT_US",
            #   "atomCount": 2,
            #   "cVMemberCount": 0,
            #   "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/attributes",
            #   "atoms": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/atoms",
            #   "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/ancestors",
            #   "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/parents",
            #   "children": null,
            #   "descendants": null,
            #   "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/relations",
            #   "definitions": null,
            #   "concepts": "https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=75508005&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi",
            #   "defaultPreferredAtom": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/atoms/preferred",
            #   "subsetMemberships": [
            #     {
            #       "memberUri": "https://uts-ws.nlm.nih.gov/rest/subsets/2021AB/source/SNOMEDCT_US/900000000000497000/member/75508005",
            #       "uri": "https://uts-ws.nlm.nih.gov/rest/subsets/2021AB/source/SNOMEDCT_US/900000000000497000",
            #       "name": "CTV3 simple map"
            #     }
            #   ],
            #   "contentViewMemberships": [],
            #   "name": "Dissecting"
            # }

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: concept Dict or None
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}"
        return self._get_single_result(uri)

    def get_source_relations(
        self,
        source_vocab: str,
        concept_id: str,
        **params,
    ) -> Iterator[Dict]:
        """
        Get a "Source Asserted" relations

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/relations/index.html>`_

        .. code-block::

             api.get_source_relations(source_vocab="MSH", concept_id="D002415",
                                        includeRelationLabels="RN,CHD", language="ENG")
            # [
            #   {
            #     "ui": "R71237095",
            #     "suppressible": false,
            #     "sourceUi": null,
            #     "obsolete": false,
            #     "sourceOriginated": false,
            #     "rootSource": "MSH",
            #     "groupId": null,
            #     "attributeCount": 0,
            #     "classType": "AtomClusterRelation",
            #     "relatedFromId": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002415",
            #     "relatedFromIdName": "Cats",
            #     "relationLabel": "CHD",
            #     "additionalRelationLabel": "",
            #     "relatedId": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991",
            #     "relatedIdName": "Felis"
            #   }
            # ]

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator over concept Dicts
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/relations"

        return self._get_results(uri, **params)

    def get_source_parents(
        self,
        source_vocab: str,
        concept_id: str,
    ) -> Iterator[Dict]:

        """
        Get a "Source Asserted" parents

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/parents-and-children/index.html>`_

        .. code-block:: python

             list(api.get_source_parents(source_vocab="MSH", concept_id="D002415"))
            # [
            #   {
            #     "classType": "SourceAtomCluster",
            #     "ui": "D045991",
            #     "suppressible": false,
            #     "obsolete": false,
            #     "rootSource": "MSH",
            #     "atomCount": 1,
            #     "cVMemberCount": 0,
            #     "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/attributes",
            #     "atoms": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/atoms",
            #     "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/ancestors",
            #     "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/parents",
            #     "children": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/children",
            #     "descendants": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/descendants",
            #     "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/relations",
            #     "definitions": null,
            #     "concepts": "https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=D045991&sabs=MSH&searchType=exact&inputType=sourceUi",
            #     "defaultPreferredAtom": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/atoms/preferred",
            #     "subsetMemberships": [],
            #     "contentViewMemberships": [],
            #     "name": "Felis"
            #   }
            # ]

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator over concept Dicts
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/parents"

        return self._get_results(uri)

    def get_source_ancestors(
        self,
        source_vocab: str,
        concept_id: str,
    ) -> Iterator[Dict]:
        """
        Get a "Source Asserted" ancestors

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/ancestors-and-descendants/index.html>`_

        .. code-block:: python

            list(api.get_source_ancestors(**kwargs))
            # [{'ancestors': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/ancestors',
            #   'atomCount': 1,
            #   'atoms': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/atoms',
            #   'attributes': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/attributes',
            #   'cVMemberCount': 0,
            #   'children': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/children',
            #   'classType': 'SourceAtomCluster',
            #   'concepts': 'https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=D002335&sabs=MSH&searchType=exact&inputType=sourceUi',
            #   'contentViewMemberships': [],
            #   'defaultPreferredAtom': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/atoms/preferred',
            #   'definitions': None,
            #   'descendants': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/descendants',
            #   'name': 'Carnivora',
            #   'obsolete': False,
            #   'parents': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/parents',
            #   'relations': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/relations',
            #   'rootSource': 'MSH',
            #   'subsetMemberships': [],
            #   'suppressible': False,
            #   'ui': 'D002335'},
            #  ...]

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator over concept Dicts
        """
        source_vocab = validate_vocab_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/ancestors"

        return self._get_results(uri)
