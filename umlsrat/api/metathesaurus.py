import argparse
import functools
import logging
import operator
from typing import Dict, Iterator, List, Optional, Tuple

from umlsrat import const
from umlsrat.api.rat_session import MetaThesaurusSession


class MetaThesaurus(object):
    """
    `UMLS MetaThesaurus API <https://documentation.uts.nlm.nih.gov/rest/home.html>`_ interface with caching.
    """

    def __init__(
        self,
        session: Optional[MetaThesaurusSession] = None,
        umls_version: Optional[str] = None,
    ):
        """
        Constructor.

        :param session: session object. If not provided, a default session will be constructed.
        See :py:meth:umlsrat.api.rat_session.MetaThesaurusSession.__init__

        :param umls_version: version of UMLS ('current' for latest).
        Defaults to :py:const:umlsrat.const.DEFAULT_UMLS_VERSION
        """

        if session:
            self.session = session
        else:
            self.session = MetaThesaurusSession()

        if umls_version:
            self.umls_version = umls_version
        else:
            self.umls_version = const.DEFAULT_UMLS_VERSION

        self._rest_uri = "https://uts-ws.nlm.nih.gov/rest"

        if self.session.use_cache and self.umls_version == "current":
            # may want to simply disable caching if version is 'current'
            self._logger.warning(
                "Version is 'current' and caching is enabled! "
                "API contents may change while the cache will not unless "
                "cleared."
            )

    @staticmethod
    def add_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Add constructor arguments to parser.

        :param parser: parser
        :return: the same parser
        """
        parser = MetaThesaurusSession.add_args(parser)

        group = parser.add_argument_group("MetaThesaurus")
        group.add_argument(
            "--umls-version",
            type=str,
            help="UMLS version to use",
            default=const.DEFAULT_UMLS_VERSION,
        )

        return parser

    @staticmethod
    def from_namespace(args: argparse.Namespace) -> "MetaThesaurus":
        """
        Construct new object using values from namespace.

        :param args: parsed args
        :return: new instance
        """
        return MetaThesaurus(
            session=MetaThesaurusSession.from_namespace(args),
            umls_version=args.umls_version,
        )

    @property
    def _logger(self):
        return logging.getLogger(self.__class__.__name__)

    #### UMLS ####

    @property
    def _start_content_uri(self) -> str:
        """http://uts-ws.nlm.nih.gov/rest/content/{self.version}"""
        return f"{self._rest_uri}/content/{self.umls_version}"

    def get_concept(self, cui: str) -> Dict:
        """
        Get a UMLS concept by CUI.


        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> MetaThesaurus().get_concept("C0009044")

        .. code-block:: js

            {
            "ui": "C0009044",
            "name": "Closed fracture of carpal bone",
            "dateAdded": "09-30-1990",
            "majorRevisionDate": "03-16-2016",
            "classType": "Concept",
            "suppressible": false,
            "status": "R",
            "semanticTypes": [
             {
               "name": "Injury or Poisoning",
               "uri": "https://uts-ws.nlm.nih.gov/rest/semantic-network/2021AB/TUI/T037"
             }
            ],
            "atoms": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044/atoms",
            "definitions": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044/definitions",
            "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044/relations",
            "defaultPreferredAtom": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044/atoms/preferred",
            "atomCount": 71,
            "cvMemberCount": 0,
            "attributeCount": 0,
            "relationCount": 5
            }

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/concept/index.html>`__

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :return: Concept
        """
        assert cui
        uri = f"{self._start_content_uri}/CUI/{cui}"
        return self.session.get_single_result(uri)

    def get_definitions(
        self, cui: str, max_results: Optional[int] = None
    ) -> Iterator[Dict]:
        """
        Get the definitions for a concept.

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> list(MetaThesaurus().get_definitions("C0009044"))

        .. code-block:: js

             [
               {
                 "rootSource": "NCI",
                 "value": "A traumatic break in one or more of the carpal bones that does not involve a break in the adjacent skin.",
                 "classType": "Definition",
                 "sourceOriginated": true
               }
             ]

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/definitions/index.html>`__

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Definition info objects
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/definitions"
        return self.session.get_results(uri, max_results=max_results)

    def get_relations(
        self, cui: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Get relations for a concept

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/relations/index.html>`__

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> list(MetaThesaurus().get_relations("C0009044"))

        .. code-block:: js

            [
              {
                "ui": "R03033072",
                "suppressible": false,
                "sourceUi": null,
                "obsolete": false,
                "sourceOriginated": false,
                "rootSource": "MTH",
                "relationLabel": "RO",
                "additionalRelationLabel": "",
                "groupId": null,
                "relatedId": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009353",
                "relatedIdName": "Colles' Fracture",
                "classType": "ConceptRelation",
                "attributeCount": 0
              },
              ...
            ]

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Relation info objects
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/relations"
        return self.session.get_results(uri, max_results=max_results, **params)

    def get_atoms_for_cui(
        self, cui: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Get Atoms for a concept.

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/atoms/index.html>`__

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> list(MetaThesaurus().get_atoms_for_cui(cui="C0009044", language="ENG"))

        .. code-block:: js

            [
              {
                "classType": "Atom",
                "ui": "A0243916",
                "sourceDescriptor": null,
                "sourceConcept": null,
                "concept": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044",
                "obsolete": "false",
                "suppressible": "false",
                "rootSource": "RCD",
                "termType": "PT",
                "code": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/RCD/S240.",
                "language": "ENG",
                "name": "Closed fracture of carpal bone",
                "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/attributes",
                "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/relations",
                "children": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/children",
                "descendants": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/descendants",
                "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/parents",
                "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/ancestors",
                "contentViewMemberships": [
                  {
                    "memberUri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357/member/A0243916",
                    "name": "MetaMap NLP View",
                    "uri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357"
                  }
                ]
              },
              ...
            ]

        :param cui: Concept Unique Identifier (CUI) for the UMLS concept
        :param max_results: maximum number of result to return. None = no max
        :param params: additional params passed to the GET request See `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/atoms/index.html>`__
        :return: list of Relation info objects
        """
        uri = f"{self._start_content_uri}/CUI/{cui}/atoms"
        return self.session.get_results(uri, max_results=max_results, **params)

    def get_atom(self, aui: str) -> Optional[Dict]:
        """
        Get Atoms for a concept.

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/atoms/index.html>`__

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> list(MetaThesaurus().get_atom(aui="A0243916"))

        .. code-block:: js

            {
              "classType": "Atom",
              "ui": "A0243916",
              "sourceDescriptor": null,
              "sourceConcept": null,
              "concept": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0009044",
              "obsolete": "false",
              "suppressible": "false",
              "rootSource": "RCD",
              "termType": "PT",
              "code": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/RCD/S240.",
              "language": "ENG",
              "name": "Closed fracture of carpal bone",
              "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/attributes",
              "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/relations",
              "children": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/children",
              "descendants": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/descendants",
              "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/parents",
              "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0243916/ancestors",
              "contentViewMemberships": [
                {
                  "memberUri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357/member/A0243916",
                  "name": "MetaMap NLP View",
                  "uri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357"
                }
              ]
            }

        :param aui: Atom Unique Identifier (AUI)
        :return: atom information
        """
        url = f"{self._start_content_uri}/AUI/{aui}"
        return self.session.get_single_result(url)

    def get_atom_ancestors(
        self, aui: str, max_results: Optional[int] = None
    ) -> Iterator[Dict]:
        """
        Get ancestors of an Atom

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/atoms/ancestors-and-descendants/index.html>`__

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> list(MetaThesaurus().get_atom_ancestors(aui="A0243916"))

        .. code-block:: js

            [
              {
                "classType": "Atom",
                "ui": "A0004658",
                "sourceDescriptor": null,
                "sourceConcept": null,
                "concept": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0016658",
                "obsolete": "false",
                "suppressible": "false",
                "rootSource": "RCD",
                "termType": "PT",
                "code": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/RCD/XA0FK",
                "language": "ENG",
                "name": "Fracture",
                "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/attributes",
                "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/relations",
                "children": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/children",
                "descendants": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/descendants",
                "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/parents",
                "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/AUI/A0004658/ancestors",
                "contentViewMemberships": [
                  {
                    "memberUri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357/member/A0004658",
                    "name": "MetaMap NLP View",
                    "uri": "https://uts-ws.nlm.nih.gov/rest/content-views/2021AB/CUI/C1700357"
                  }
                ]
              },
              ...
            ]

        :param aui: Atom Unique Identifier (AUI) for the UMLS Atom
        :param max_results: maximum number of result to return. None = no max
        :return: generator yielding Concepts
        """
        assert aui.startswith("A"), f"Invalid AUI '{aui}'"
        uri = f"{self._start_content_uri}/AUI/{aui}/ancestors"
        return self.session.get_results(uri, max_results=max_results)

    ###
    # Search
    ###

    def search(
        self, query: str, max_results: Optional[int] = None, **params
    ) -> Iterator[Dict]:
        """
        Search UMLS!

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/search/index.html>`__

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> MetaThesaurus().search("cheese", max_results=1)

        .. code-block:: js

            [
              {
                "ui": "C0007968",
                "rootSource": "MTH",
                "uri": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/CUI/C0007968",
                "name": "Cheese"
              }
            ]

        :param query: search string
        :param max_results: maximum number of result to return. None = no max
        :param params: additional get request params
        :return: generator yielding search results
        """
        uri = f"https://uts-ws.nlm.nih.gov/rest/search/{self.umls_version}"
        if "string" in params:
            self._logger.warning(
                "Overwriting existing 'string' value %s", params["string"]
            )
        params["string"] = query
        return self.session.get_results(uri, max_results=max_results, **params)

    ###
    # Source Asserted
    ####

    def get_source_concept(self, source_vocab: str, concept_id: str) -> Optional[Dict]:
        """
        Get a source asserted concept. e.g. a concept from SNOMED, LOINC, etc

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/index.html>`__

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> MetaThesaurus().get_source_concept(source_vocab="snomed", concept_id="75508005")

        .. code-block:: js

            {
              "classType": "SourceAtomCluster",
              "ui": "75508005",
              "suppressible": false,
              "obsolete": false,
              "rootSource": "SNOMEDCT_US",
              "atomCount": 2,
              "cVMemberCount": 0,
              "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/attributes",
              "atoms": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/atoms",
              "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/ancestors",
              "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/parents",
              "children": null,
              "descendants": null,
              "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/relations",
              "definitions": null,
              "concepts": "https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=75508005&sabs=SNOMEDCT_US&searchType=exact&inputType=sourceUi",
              "defaultPreferredAtom": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/SNOMEDCT_US/75508005/atoms/preferred",
              "subsetMemberships": [
                {
                  "memberUri": "https://uts-ws.nlm.nih.gov/rest/subsets/2021AB/source/SNOMEDCT_US/900000000000497000/member/75508005",
                  "uri": "https://uts-ws.nlm.nih.gov/rest/subsets/2021AB/source/SNOMEDCT_US/900000000000497000",
                  "name": "CTV3 simple map"
                }
              ],
              "contentViewMemberships": [],
              "name": "Dissecting"
            }

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: concept or None
        """
        source_vocab = self.validate_source_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}"
        return self.session.get_single_result(uri)

    def get_source_relations(
        self,
        source_vocab: str,
        concept_id: str,
        **params,
    ) -> Iterator[Dict]:
        """
        Get source asserted relations

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/relations/index.html>`__

        .. code-block:: python

            from umlsrat.api.metathesaurus import MetaThesaurus
            list(MetaThesaurus().get_source_relations(source_vocab="MSH",
                                                      concept_id="D002415",
                                                      includeRelationLabels="RN,CHD",))


        .. code-block:: js

            [
              {
                "ui": "R71237095",
                "suppressible": false,
                "sourceUi": null,
                "obsolete": false,
                "sourceOriginated": false,
                "rootSource": "MSH",
                "groupId": null,
                "attributeCount": 0,
                "classType": "AtomClusterRelation",
                "relatedFromId": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002415",
                "relatedFromIdName": "Cats",
                "relationLabel": "CHD",
                "additionalRelationLabel": "",
                "relatedId": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991",
                "relatedIdName": "Felis"
              }
            ]

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator yielding concepts
        """
        source_vocab = self.validate_source_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/relations"

        return self.session.get_results(uri, **params)

    def get_source_parents(
        self,
        source_vocab: str,
        concept_id: str,
    ) -> Iterator[Dict]:

        """
        Get source asserted parents

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/parents-and-children/index.html>`__

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> list(MetaThesaurus().get_source_parents(source_vocab="MSH", concept_id="D002415"))


        .. code-block:: python

            [
              {
                "classType": "SourceAtomCluster",
                "ui": "D045991",
                "suppressible": false,
                "obsolete": false,
                "rootSource": "MSH",
                "atomCount": 1,
                "cVMemberCount": 0,
                "attributes": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/attributes",
                "atoms": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/atoms",
                "ancestors": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/ancestors",
                "parents": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/parents",
                "children": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/children",
                "descendants": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/descendants",
                "relations": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/relations",
                "definitions": null,
                "concepts": "https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=D045991&sabs=MSH&searchType=exact&inputType=sourceUi",
                "defaultPreferredAtom": "https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D045991/atoms/preferred",
                "subsetMemberships": [],
                "contentViewMemberships": [],
                "name": "Felis"
              }
            ]

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator yielding concepts
        """
        source_vocab = self.validate_source_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/parents"

        return self.session.get_results(uri)

    def get_source_ancestors(
        self,
        source_vocab: str,
        concept_id: str,
    ) -> Iterator[Dict]:
        """
        Get source asserted ancestors

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/ancestors-and-descendants/index.html>`__

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> list(MetaThesaurus().get_source_ancestors(source_vocab="MSH", concept_id="D002415"))

        .. code-block:: python

            [{'ancestors': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/ancestors',
              'atomCount': 1,
              'atoms': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/atoms',
              'attributes': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/attributes',
              'cVMemberCount': 0,
              'children': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/children',
              'classType': 'SourceAtomCluster',
              'concepts': 'https://uts-ws.nlm.nih.gov/rest/search/2021AB?string=D002335&sabs=MSH&searchType=exact&inputType=sourceUi',
              'contentViewMemberships': [],
              'defaultPreferredAtom': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/atoms/preferred',
              'definitions': None,
              'descendants': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/descendants',
              'name': 'Carnivora',
              'obsolete': False,
              'parents': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/parents',
              'relations': 'https://uts-ws.nlm.nih.gov/rest/content/2021AB/source/MSH/D002335/relations',
              'rootSource': 'MSH',
              'subsetMemberships': [],
              'suppressible': False,
              'ui': 'D002335'},
             ...]

        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :return: generator yielding concepts
        """
        source_vocab = self.validate_source_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._start_content_uri}/source/{source_vocab}/{concept_id}/ancestors"

        return self.session.get_results(uri)

    def crosswalk(
        self, source_vocab: str, concept_id: str, language: str = None, **params
    ) -> Iterator[Dict]:
        """
        Crosswalk vocabularies. Find all source atoms which share the same CUI.

        `UMLS Doc <https://documentation.uts.nlm.nih.gov/rest/source-asserted-identifiers/crosswalk/>`__


        :param source_vocab: source Vocabulary
        :param concept_id: concept ID
        :param language: target language
        :return: generator yielding atom clusters
        """
        source_vocab = self.validate_source_abbrev(source_vocab)
        assert concept_id
        uri = f"{self._rest_uri}/crosswalk/{self.umls_version}/source/{source_vocab}/{concept_id}"

        if language:
            params["targetSource"] = self.get_sabs_str(
                language, params.pop("targetSource", None)
            )

        return self.session.get_results(uri, **params)

    ##
    # Source vocabulary metadata and lookup.
    ##
    @property
    def _source_metadata(self) -> Iterator[Dict]:
        """
        Get metadata for UMLS sources.

        :return: list of metadata about sources
        """
        url = f"{self._rest_uri}/metadata/{self.umls_version}/sources"
        return self.session.get_results(url)

    @property
    @functools.lru_cache()
    def source_metadata_index(self) -> Dict[str, Dict]:
        """
        Get source metadata indexed by abbreviation.

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> MetaThesaurus().source_metadata_index.get("LNC")

        .. code-block: js

            {
              "classType": "RootSource",
              "abbreviation": "LNC",
              "expandedForm": "LOINC, 271",
              "family": "LNC",
              "language": {
                "classType": "Language",
                "abbreviation": "ENG",
                "expandedForm": "English"
              },
              "restrictionLevel": 0,
              ...
            }

        :return: source metadata indexed by abbreviation
        """
        index = {}
        for datum in self._source_metadata:
            abbr = datum["abbreviation"]
            assert abbr not in index
            index[abbr] = datum
        return index

    def find_source_info(self, name: str, fuzzy: bool = False) -> Optional[Dict]:
        """
        Find metadata for a source vocabulary.

        :param name: the abbreviation or name of the vocab
        :param fuzzy: do a fuzzy match on non abbreviation fields (i.e. "shortName")
        :return: source info or None if it cannot be found
        """
        data = self.source_metadata_index.get(name)
        if data:
            return data

        abbr_upper = name.upper()
        data = self.source_metadata_index.get(abbr_upper)
        if data:
            return data

        abbr_mapped = const._COMMON_VOCAB_NAMES.get(abbr_upper)
        data = self.source_metadata_index.get(abbr_mapped)
        if data:
            return data

        if not fuzzy:
            return None

        # fuzzy matching
        candidates = list(self.source_metadata_index.values())

        def match_field(field_name: str, op):
            results = list()
            for c in candidates:
                if c[field_name] and op(c[field_name].upper(), abbr_upper):
                    results.append(c)
            if not results:
                return None

            if len(results) == 1:
                return results.pop()
            else:
                raise ValueError(
                    f"Ambiguous vocab abbr '{name}' -- fuzzy match returned {len(results)} results.\n"
                    f"{[_[field_name] for _ in results]}"
                )

        data = match_field("shortName", operator.eq)
        if data:
            return data

        data = match_field("shortName", operator.contains)
        if data:
            return data

        # no match
        return None

    def validate_source_abbrev(self, sab: str) -> str:
        """
        Look up the source info for the abbreviation. If it exists, return the properly normalized
        abbreviation. Otherwise, raise.

        .. code-block: python
            from umlsrat.api.metathesaurus import MetaThesaurus

            MetaThesaurus().validate_source_abbrev("snomed")
            # "SNOMEDCT_US"

            MetaThesaurus().validate_source_abbrev("loinx")
            # raises ValueError

        :param sab: source abbreviation
        :return: normalized source abbreviation
        :raises ValueError: when abbreviation is invalid
        """
        info = self.find_source_info(sab)
        if not info:
            raise ValueError(f"No such vocabulary abbreviation '{sab}'")
        else:
            return info["abbreviation"]

    @functools.lru_cache(maxsize=2)
    def sources_for_language(self, lab: str) -> Tuple[str]:
        """
        Get a list of source abbreviations associated with a given language (abbreviation).

        >>> from umlsrat.api.metathesaurus import MetaThesaurus
        >>> MetaThesaurus().sources_for_language("GER")

        .. code-block: js

            ('DMDICD10', 'DMDUMD', 'ICPCGER', 'LNC-DE-AT',
                'LNC-DE-DE', 'MDRGER', 'MSHGER', 'WHOGER')

        :param lab: language abbreviation
        :return: list of source abbreviations
        """
        sabs_list = [
            source["abbreviation"]
            for source in self.source_metadata_index.values()
            if source["language"]["abbreviation"] == lab
        ]  # type: List[str]
        return tuple(sorted(sabs_list))

    def validate_language_abbrev(self, lab: str) -> str:
        """
        Look up the sources for language. If any exist, return the properly normalized language
        abbreviation. Otherwise, raise.

        .. code-block: python
            from umlsrat.api.metathesaurus import MetaThesaurus

            MetaThesaurus().validate_language_abbrev("fre")
            # "FRE"

            MetaThesaurus().validate_language_abbrev("FRA")
            # raises ValueError

        :param lab: language abbreviation
        :return: normalized abbreviation
        :raises ValueError: if no sources exist for the language
        """
        assert lab, "must supply language abbreviation"
        abbr_upper = lab.upper()
        if self.sources_for_language(abbr_upper):
            return abbr_upper
        raise ValueError(f"No sources found for language abbrev '{lab}'")

    def _valid_ordered_split_sabs(self, sabs_str: str) -> List[str]:
        # maintaining order is important for caching
        return sorted(
            set(self.validate_source_abbrev(_.strip()) for _ in sabs_str.split(","))
        )

    def get_sabs_str(self, language: str, sabs: Optional[str] = None) -> str:
        """
        Return a comma-separated list of source abbreviations for a target language. If asabs string
        is provided, we simply validate that it belongs to the target language.

        :param language: target language
        :param sabs: comma-separated list of source abbreviations
        :return:
        """
        if not language:
            if not sabs:
                return ""
            else:
                # simply validate the sabs
                return ",".join(self._valid_ordered_split_sabs(sabs))

        lab = self.validate_language_abbrev(language)
        lang_sab_tpl = self.sources_for_language(lab)

        if sabs:
            existing = self._valid_ordered_split_sabs(sabs)
            existing_set = set(existing)
            lang_sab_set = set(lang_sab_tpl)
            not_in_language = existing_set - lang_sab_set
            if not_in_language:
                raise ValueError(
                    f"{not_in_language} source vocabularies are not associated with language '{language}'"
                )
            # so if you have specified sabs already, we just validate them and send them back
            return sabs
        else:
            return ",".join(lang_sab_tpl)
